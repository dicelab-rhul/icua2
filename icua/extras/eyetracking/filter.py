"""Module defines some common eyetracking filters that can be used with an `Eyetracker`.

Filter classes:
- `NanValidator`
- `NWMAFilter` (Non-weighted Moving Average Filter)
- `IVTFilter` (Velocity-Threshold Identification Filter)
- `WindowSpaceFilter`

See class documentation for details.
"""

from typing import Any
from collections import deque
import math
import time
from ...utils import LOGGER

__all__ = ("NWMAFilter", "WindowSpaceFilter", "IVTFilter", "NanValidator")


class NanValidator:
    """A filter that validates the stream of eyetracking events. It looks for long periods of inactivity or continuous Nan values, and if these reach a duration threshold then an error or warning is raised."""

    def __init__(
        self, duration: float, should_warn: bool = True, should_error: bool = False
    ):
        """Constructor.

        Args:
            duration (float): duration to wait before error/warning if the eyetracker is inactive or sends too many nan values.
            should_warn (bool, optional): whether to warn if eyetracking data is deemed invalid. Defaults to True.
            should_error (bool, optional): whether to raise an error if the eyetracking data is deemed invalid. Defaults to False.
        """
        super().__init__()
        self._duration = duration
        self._start_time = None  # set when the first nan event is received
        self._last_event = None
        self._should_warn = should_warn
        self._should_error = should_error
        self._nan_count = 0

    def __call__(self, data: dict[str, Any]) -> dict[str, Any]:
        """Checks the eyetracking data for long periods of inactivity of NaN values and raises an error (or warns) if this happens. Leaves the eyetracking input `data` unchanged.

        Args:
            data (dict[str, Any]): eyetracking data

        Returns:
            dict[str, Any]: eyetracking data
        """
        x, y = data["position"]
        now = time.time()
        # check if there has been a large gap between eyetracking events - probably there is an issue!
        if self._last_event is not None:
            if now - self._last_event > self._duration:
                self._bad_eyetracker(now - self._last_event)
        self._last_event = now

        # check if we have received many nan values in a row - probably there is an issue!
        is_nan = x != x or y != y
        if is_nan:
            self._nan_count += 1
            if self._start_time is None:
                self._start_time = now
        else:
            self._start_time = None

        # we are seeing nan values for some period of time...
        if self._start_time is not None:
            bad_duration = now - self._start_time
            if bad_duration > self._duration:
                self._bad_eyetracker(bad_duration)
        return data

    def _bad_eyetracker(self, bad_duration: float):
        if self._should_warn:
            LOGGER.warning(
                f"Eyetracker has received bad data for: {bad_duration:.2f}s, Nan count: {self._nan_count}"
            )
        if self._should_error:
            raise ValueError(
                f"Eyetracker has received bad data for: {bad_duration:.2f}s, Nan count: {self._nan_count}"
            )


class NWMAFilter:  # Non-weighted moving average
    """Filter that computes a moving average over eye gaze positions for some window size."""

    def __init__(self, n: int):
        """Constructor.

        Args:
            n (int): window size of the moving average.
        """
        super().__init__()
        self.data_x = deque(maxlen=n)
        self.data_y = deque(maxlen=n)

    def __call__(self, data: dict[str, Any]) -> dict[str, Any]:
        """Compute the moving average. Expects a `position` attribute in `data` and will modify this attribute in-place.

        Args:
            data (dict[str, Any]): eyetracking data.

        Returns:
            dict[str, Any]: filtered eyetracking data.
        """
        x, y = data["position"]
        # print("nwma:", x, y)
        if math.isnan(x) or math.isnan(y):
            return data  # ignore this sample
        self.data_x.append(x)
        self.data_y.append(y)
        x = sum(self.data_x) / len(self.data_x)
        y = sum(self.data_y) / len(self.data_y)
        data["position"] = (x, y)
        return data

    def __str__(self) -> str:  # noqa
        return f"{NWMAFilter}(N={len(self.data_x)})"

    def __repr__(self) -> str:  # noqa
        return str(self)


class WindowSpaceFilter:
    """Filter that will transform eye gaze positions from screen space to window coordinate space."""

    def __init__(
        self,
        screen_size: tuple[float, float],
        window_size: tuple[float, float],
        window_position: tuple[float, float],
        keep_screen_data: bool = True,
    ):
        """Constructor.

        Args:
            screen_size (tuple[float, float]): size of the screen/computer monitor.
            window_size (tuple[float, float]): size of the UI window.
            window_position (tuple[float, float]): position of the UI window on the screen.
            keep_screen_data (bool): whether to preserve the screen data (position/velocity). If True then the fields `position_screen` and `velocity_screen` will be added, otherwise this information will be lost as `position` and `velocity` are modified in place.
        """
        super().__init__()
        self.screen_size = screen_size
        self.window_size = window_size
        self.window_position = window_position
        self._keep_screen_data = keep_screen_data

    def __call__(self, data: dict[str, Any]) -> dict[str, Any]:
        """Compute the screen->window space transformation. Expects a `position` attribute in `data` and will modify this attribute in-place. It will also transform the `velocity` attribute if it is found.

        This filter expects the screen coordinates to be in the range (0,1). It also assumes that the screen and the window share the same origin (0,0) being the top-left. The screen->window transformation is computed as:
        ```
        x *= screen_width
        y *= screen_height
        x -= window_x
        y -= window_y
        ```

        which is the default for many eyetrackers.
        If `keep_screen_data` is True then new attributes: `position_screen` and `position_velocity` will be added to preserve the screen position/velocity.

        Args:
            data (dict[str, Any]): eyetracking data.

        Returns:
            dict[str, Any]: filtered eyetracking data.
        """
        x, y = data["position"]
        # print("window:", x, y)
        if math.isnan(x) or math.isnan(y):
            data["in_window"] = False
            if self._keep_screen_data:
                data["position_screen"] = data["position"]
                if "velocity" in data:
                    data["velocity_screen"] = data["velocity"]
            return data

        position_screen = (x, y)
        if not (0 <= x <= 1 and 0 <= y <= 1.0):
            LOGGER.warning(
                f"Expected eyetracking coordinates in the range [0-1], received: {position_screen}."
            )
        x *= self.screen_size[0]
        y *= self.screen_size[1]
        x -= self.window_position[0]
        y -= self.window_position[1]
        in_window = (
            x > 0 and x < self.window_size[0] and y > 0 and y < self.window_size[1]
        )
        # print((x, y), self.screen_size, self.window_size)
        data["in_window"] = in_window
        data["position"] = (x, y)
        if self._keep_screen_data:
            data["position_screen"] = position_screen
        if "velocity" in data:
            vx, vy = data["velocity"]
            data["velocity"] = (vx * self.screen_size[0], vy * self.screen_size[1])
            if self._keep_screen_data:
                data["velocity_screen"] = (vx, vy)
        return data


class IVTFilter:
    """Velocity-Threshold Identification Filter (loosely based on http://www.vinis.co.kr/ivt_filter.pdf).

    This will filter will attempt to determine whether the eyes are fixated or saccading based on their velocity. The implementation computes positional velocity rather than anglular velocity (which is a departure from the original algorithm). The reason is that gaze angle may not be avaliable in the eyetracking event data.

    The `fixated` and `velocity` attributes will be added to eyetracking event data. `fixated` will be True if the velocity is below the threshold and False otherwise (indicating a saccade).

    IMPORTANT: The `velocity_threshold` is there for sensitive to the coordinate system that is in use, so be aware when using this along side coordinate space transformation filters.
    """

    def __init__(self, velocity_threshold: float):
        """Constructor.

        Args:
            velocity_threshold (float): velocity threshold used to determine whether the eye is fixated or saccading.
        """
        self.data_x = deque(maxlen=2)
        self.data_y = deque(maxlen=2)
        self.data_t = deque(maxlen=2)
        self.velocity_threshold = velocity_threshold

    def __call__(self, data: dict[str, Any]) -> dict[str, Any]:
        """Computes fixation/saccade based on velocity threshold. The velocity is estimated based on the two most recent positions and their associated timestamps. The first event will always be treated as a fixation. The filter assumes that the `position` and `timestamp` attribute are present in `data`.

        The `fixated` and `velocity` attributes will be added to eyetracking event data. `fixated` will be True if the velocity is below the threshold and False otherwise (indicating a saccade).

        Args:
            data (dict[str, Any]): eyetracking data.

        Returns:
            dict[str, Any]: filtered eyetracking data.
        """
        x, y = data["position"]
        t = data["timestamp"]
        # print("ivt:", x, y)

        if math.isnan(x) or math.isnan(y):
            data["fixated"] = False
            data["velocity"] = (float("nan"), float("nan"))
            return data  # ignore the data point

        # estimate velocity using the two most recent samples...
        self.data_x.append(x)
        self.data_y.append(y)
        self.data_t.append(t)
        dt = self.data_t[-1] - self.data_t[0]
        if dt > 0:
            dx = self.data_x[-1] - self.data_x[0]
            dy = self.data_y[-1] - self.data_y[0]
            speed = math.sqrt(dx**2 + dy**2) / dt
            data["velocity"] = (dx / dt, dy / dt)
        elif dt == 0:
            speed = 0
            data["velocity"] = (0, 0)
        else:
            raise ValueError(f"Negative dt: {dt} was found in {IVTFilter.__name__}.")
        data["fixated"] = speed <= self.velocity_threshold
        return data
