from typing import List, Dict, Tuple, Callable, Any
import math
from star_ray.agent import Actuator, Sensor, attempt, RoutedActionAgent
from star_ray.environment.wrapper_state import _State
from star_ray.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
)
from star_ray.event.user_event import (
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    WindowCloseEvent,
)
from star_ray_pygame.avatar import Avatar as PygameAvatar
from star_ray_pygame import WindowConfiguration

from icua2.extras.eyetracking import (
    EyetrackerWithUI,
    EyeMotionEvent,
    WindowSpaceFilter,
    NWMAFilter,
    IVTFilter,
)
from .default_actuator import DefaultActuator


class Avatar(PygameAvatar):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        eyetracker: EyetrackerWithUI = None,
        window_config: WindowConfiguration = None,
        **kwargs
    ):
        # see `DefaultActuator` documentation
        actuators.append(DefaultActuator())
        super().__init__(sensors, actuators, window_config=window_config, **kwargs)
        self._eyetracker = eyetracker
        if self._eyetracker:
            # add event callbacks for eyetracker for when/if the ui window is moved or resized
            self.add_event_callback(
                WindowMoveEvent, self._eyetracker.on_window_move_event
            )
            self.add_event_callback(
                WindowResizeEvent, self._eyetracker.on_window_resize_event
            )

    def on_window_move_event(self, event: WindowMoveEvent):
        return super().on_window_move_event(event)

    def on_window_resize_event(self, event: WindowResizeEvent):
        return super().on_window_resize_event(event)

    @property
    def is_eyetracking(self):
        # perhaps do some additional checks? like whether events are actually being generated?
        return not self._eyetracker is None

    def __initialise__(self, state):
        if self._eyetracker:
            self._eyetracker.start()
        return super().__initialise__(state)

    def __cycle__(self):
        if self._eyetracker:
            events = self._eyetracker.get_nowait()
            self.__attempt__(events)
        super().__cycle__()

    def __terminate__(self):
        if self._eyetracker:
            self._eyetracker.stop()
        return super().__terminate__()

    @staticmethod
    def get_default_eyetracker(
        eyetracker_base_uri: str = None,
        moving_average_n: int = 5,
        velocity_threshold: float = 10,
    ):
        nan = (float("nan"), float("nan"))

        # create filters
        maf = NWMAFilter(n=moving_average_n)
        ivf = IVTFilter(velocity_threshold=velocity_threshold)
        # this filter will be set up when the eyetracker is created!
        wsf = WindowSpaceFilter(nan, nan, nan)

        # TODO try some other eyetrackers providers? when they are implemented in icua2
        from icua2.extras.eyetracking.tobii import (
            TobiiEyetracker,
            TOBII_RESEACH_SDK_AVALIABLE,
        )

        if not TOBII_RESEACH_SDK_AVALIABLE:
            raise ValueError(
                "Failed to create tobii eyetracker, tobii research sdk is not avalible on this system.\nTry installing it with `pip install tobii-research`, or add the optional extra `pip install matbii[tobii]`"
            )
        eyetracker_base = TobiiEyetracker(
            uri=eyetracker_base_uri, filters=[maf, ivf, wsf]
        )

        def _eyemotioneventfactory(data):
            return EyeMotionEvent(**data)

        return EyetrackerWithUI(eyetracker_base, _eyemotioneventfactory, nan, nan, nan)
