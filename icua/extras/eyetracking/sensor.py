"""Module defines the `EyetrackerIOSensor` class which may be attached to an agent to receive `EyeMotionEvent`s as user input, see class documentation for details."""

from star_ray.agent import IOSensor, attempt
from .eyetrackerbase import EyetrackerBase
from .filter import IVTFilter, WindowSpaceFilter, NWMAFilter, NanValidator
from .event import EyeMotionEventRaw, EyeMotionEvent
from ...event import WindowResizeEvent, WindowMoveEvent, ScreenSizeEvent


class EyetrackerIOSensor(IOSensor):
    """An `IOSensor` implementation that gathers observations `EyeMotionEvent` from an eyetracker."""

    def __init__(
        self,
        eyetracker: EyetrackerBase,
        velocity_threshold: float = 0.1,
        moving_average: int = 10,
        invalid_duration: float = 1,
        should_error: bool = True,
    ):
        """Constructor.

        Args:
            eyetracker (EyetrackerBase): base eyetracker, this is the IO device of this `IOSensor`.
            velocity_threshold (float, optional): velocity threshold for the `IVTFilter`. Defaults to 0.1.
            moving_average (int, optional): moving average window size for the `NWMAFilter`. Defaults to 10.
            invalid_duration (float, optional): how long it is acceptable to have NaN or no eyetracking data before a warning or error is raised.
            should_error (bool, optional): whether to raise an error if the eyetracker is sending nan values, or has not sent a value for the given duration.
        """
        super().__init__(eyetracker)
        self._ivt_filter = IVTFilter(velocity_threshold)
        nan = tuple([float("nan"), float("nan")])
        self._ws_filter = WindowSpaceFilter(nan, nan, nan)
        self._ma_filter = NWMAFilter(moving_average)
        self._validator = NanValidator(duration=invalid_duration, should_warn=True, should_error=should_error)

    def __transduce__(self, events: list[EyeMotionEventRaw]) -> list[EyeMotionEvent]:
        """Converts the list of raw eyetracking events to a list of eyetracking events by appling the filters that are part of this sensor.

        The filters are applied in order:
        - `NWMAFilter` - computes a moving average over points
        - `IVTFilter` - computes fixation/saccade based on velocity threshold.
        - `WindowSpaceFilter` - computes window UI space coordinates from screen space (requires screen & window information, see methods: `EyetrackerIOSensor.on_window_move`, `EyetrackerIOSensor.on_window_resize`, `EyetrackerIOSensor.on_screen_size`).

        Args:
            events (list[EyeMotionEventRaw]): raw eyetracking events

        Returns:
            list[EyeMotionEvent]: eyetracking events
        """
        return list(self._transduce_iter(events))

    def _transduce_iter(self, events: list[EyeMotionEventRaw]):  # noqa
        # applies all filters to the each eye motion event
        for event in events:
            data = event.model_dump()
            for filter in [self._validator, self._ma_filter, self._ivt_filter, self._ws_filter, ]:
                data = filter(data)
            # NOTE: position needs to be set properly in the agent (i.e. convert to view space)
            data["position_raw"] = data["position"]
            yield EyeMotionEvent.model_validate(data)

    @attempt
    def on_window_move(self, event: WindowMoveEvent) -> None:
        """Should be called when the UI window is moved. It is the responsibility of the attached agent to provide this information to this sensor. It is required to transform raw eyetracking coordinates to UI coordinates.

        If this sensor is attached to a `AgentRouted` this may be called automatically.

        Args:
            event (WindowMoveEvent): event with information about the UI window position.
        """
        # print("WINDOW MOVE", event.position)
        self._ws_filter.window_position = event.position

    @attempt
    def on_window_resize(self, event: WindowResizeEvent) -> None:
        """Should be called when the UI window is resized. It is the responsibility of the attached agent to provide this information to this sensor. It is required to transform raw eyetracking coordinates to UI coordinates.

        If this sensor is attached to a `AgentRouted` this may be called automatically.

        Args:
            event (WindowResizeEvent): event with information about the UI window size.
        """
        # print("WINDOW RESIZE!", event.size)
        self._ws_filter.window_size = event.size

    @attempt
    def on_screen_size(self, event: ScreenSizeEvent) -> None:
        """Should be called when the screen/monitor size is discovered for the first time. It is the responsibility of the attached agent to provide this information to this sensor. It is required to transform raw eyetracking coordinates to UI coordinates.

        If this sensor is attached to a `AgentRouted` this may be called automatically.

        Args:
            event (ScreenSizeEvent): event with information about the screen/monitor size.
        """
        # print("SCREEN SIZE!", event.size)
        self._ws_filter.screen_size = event.size
