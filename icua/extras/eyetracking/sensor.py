"""Module defines the :class:`EyetrackerIOSensor` class which may be attached to an agent to receive :class:`EyeMotionEvent`s as user input, see class documentation for details."""

from star_ray.agent import IOSensor, attempt
from .eyetrackerbase import EyetrackerBase
from .filter import IVTFilter, WindowSpaceFilter, NWMAFilter
from .event import EyeMotionEventRaw, EyeMotionEvent
from ...event import WindowResizeEvent, WindowMoveEvent, ScreenSizeEvent


class EyetrackerIOSensor(IOSensor):
    """An :class:`IOSensor` implementation that gathers observations :class:`EyeMotionEvent` from an eyetracker."""

    def __init__(
        self,
        eyetracker: EyetrackerBase,
        velocity_threshold: float = 0.1,
        moving_average: int = 10,
    ):
        """Constructor.

        Args:
            eyetracker (EyetrackerBase): base eyetracker, this is the IO device of this :class:`IOSensor`.
            velocity_threshold (float, optional): velocity threshold for the :class:`IVTFilter`. Defaults to 0.1.
            moving_average (int, optional): moving average window size for the :class:`NWMAFilter`. Defaults to 10.
        """
        super().__init__(eyetracker)
        self._ivt_filter = IVTFilter(velocity_threshold)
        nan = tuple([float("nan"), float("nan")])
        self._ws_filter = WindowSpaceFilter(nan, nan, nan)
        self._ma_filter = NWMAFilter(moving_average)

    def __transduce__(self, events: list[EyeMotionEventRaw]) -> list[EyeMotionEvent]:
        """Converts the list of raw eyetracking events to a list of eyetracking events by appling the filters that are part of this sensor.

        The filters are applied in order:
        - :class:`NWMAFilter` - computes a moving average over points
        - :class:`IVTFilter` - computes fixation/saccade based on velocity threshold.
        - :class:`WindowSpaceFilter` - computes window UI space coordinates from screen space (requires screen & window information, see methods: :method:`EyetrackerIOSensor.on_window_move`, :method:`EyetrackerIOSensor.on_window_resize`, :method:`EyetrackerIOSensor.on_screen_size`).

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
            for filter in [self._ma_filter, self._ivt_filter, self._ws_filter]:
                data = filter(data)
            # position needs to be set properly in the agent!
            data["position_raw"] = data["position"]
            data["position"] = tuple([float("nan"), float("nan")])
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
