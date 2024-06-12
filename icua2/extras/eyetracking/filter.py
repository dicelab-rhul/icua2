from typing import Tuple, Dict, Any
from collections import deque
import math
from .event import EyeMotionEvent

__all__ = ("NWMAFilter", "WindowSpaceFilter", "IVTFilter")


class NWMAFilter:  # Non-weighted moving average

    def __init__(self, n: int):
        super(NWMAFilter, self).__init__()
        self.data_x = deque(maxlen=n)
        self.data_y = deque(maxlen=n)

    def __call__(self, data: Dict[str, Any]) -> Dict[str, Any]:
        x, y = data["position"]
        if math.isnan(x) or math.isnan(y):
            return data  # ignore this sample
        self.data_x.append(x)
        self.data_y.append(y)
        x = sum(self.data_x) / len(self.data_x)
        y = sum(self.data_y) / len(self.data_y)
        data["position"] = (x, y)
        return data

    def __str__(self) -> str:
        return f"{NWMAFilter}(N={len(self.data_x)})"

    def __repr__(self) -> str:
        return str(self)


class WindowSpaceFilter:

    def __init__(
        self,
        screen_size: Tuple[float, float],
        window_size: Tuple[float, float],
        window_position: Tuple[float, float],
    ):
        super().__init__()
        self.screen_size = screen_size
        self.window_size = window_size
        self.window_position = window_position

    def __call__(self, data: Dict[str, Any]) -> Dict[str, Any]:
        x, y = data["position"]
        if math.isnan(x) or math.isnan(y):
            data["in_window"] = False
            data["position_screen"] = data["position"]
            return data

        position_screen = (x, y)
        x *= self.screen_size[0]
        y *= self.screen_size[1]
        x -= self.window_position[0]
        y -= self.window_position[1]
        in_window = (
            x > 0 and x < self.window_size[0] and y > 0 and y < self.window_size[1]
        )
        data["in_window"] = in_window
        data["position"] = (x, y)
        data["position_screen"] = position_screen
        return data


class IVTFilter:

    def __init__(self, velocity_threshold: float):
        self.data_x = deque(maxlen=2)
        self.data_y = deque(maxlen=2)
        self.data_t = deque(maxlen=2)
        self.velocity_threshold = velocity_threshold

    def __call__(self, data: Dict[str, Any]) -> Dict[str, Any]:
        x, y = data["position"]
        t = data["timestamp"]

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
