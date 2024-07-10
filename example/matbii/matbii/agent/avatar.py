from typing import List

from star_ray import Sensor, Actuator

from star_ray_pygame.avatar import Avatar as PygameAvatar
from star_ray_pygame import WindowConfiguration
from star_ray_pygame.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowOpenEvent,
    WindowResizeEvent,
)

from icua2.extras.eyetracking import (
    EyetrackerWithUI,
    EyeMotionEvent,
    WindowSpaceFilter,
    NWMAFilter,
    IVTFilter,
)
from .avatar_actuator import DefaultActuator


class Avatar(PygameAvatar):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        eyetracker: EyetrackerWithUI = None,
        window_config: WindowConfiguration = None,
        **kwargs,
    ):
        # see `DefaultActuator` documentation
        actuators.append(DefaultActuator())
        super().__init__(sensors, actuators, window_config=window_config, **kwargs)
        self._eyetracker = eyetracker

    @property
    def is_eyetracking(self):
        # TODO perhaps do some additional checks? like whether events are actually being generated?
        return not self._eyetracker is None

    def on_window_move_event(self, event: WindowMoveEvent):
        if self._eyetracker:
            self._eyetracker.on_window_move_event(event)

    def on_window_resize_event(self, event: WindowResizeEvent):
        if self._eyetracker:
            self._eyetracker.on_window_resize_event(event)

    def on_window_close_event(self, event: WindowCloseEvent):
        pass

    def on_window_focus_event(self, event: WindowFocusEvent):
        pass

    def on_window_open_event(self, event: WindowOpenEvent):
        pass

    def on_key_event(self, event: KeyEvent):
        pass

    def on_mouse_button_event(self, event: MouseButtonEvent):
        pass

    def on_mouse_motion_event(self, event: MouseMotionEvent):
        pass

    def __initialise__(self, state):
        if self._eyetracker:
            self._eyetracker.screen_size = self.get_screen_info()["size"]
            window_info = self.get_window_info()
            self._eyetracker.window_size = window_info["size"]
            self._eyetracker.window_position = window_info["position"]
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
        velocity_threshold: float = 0.5,
        throttle_events: int = -1,
        **kwargs,  # more?
    ):
        """Factory method for the default eyetracker. This method will search for avaliable eyetrackers and attempt to perform setup.

        Args:
            eyetracker_base_uri (str, optional): the uri of the eyetracker to use, if None then the first avaliable eyetracker will be used. Defaults to None.
            moving_average_n (int, optional): number of samples to use for the Non-Weighted Moving Average filter (see `NWMAFilter`). Defaults to 5.
            velocity_threshold (float, optional): TODO make this angle based, for now -> Velocity theshold to determine fixations/saccades. IMPORTANT: This is defined for the normalised eyetracking coordinates (between 0 and 1) and NOT the gaze angle or pixel-based coordinates. Defaults to 0.5.
            throttle_events (int, optional): _description_. Defaults to -1.

        Raises:
            ValueError: If no eyetracker could be found or eyetracker initialisation fails.

        Returns:
            EyetrackerWithUI: the eyetracker.
        """
        assert throttle_events < 0  # TODO this is not implemented yet
        nan = (float("nan"), float("nan"))
        # create filters
        maf = NWMAFilter(n=moving_average_n)
        ivf = IVTFilter(velocity_threshold=velocity_threshold)
        # this filter will be set up fully (screen/window position/size) when the eyetracker is started!
        wsf = WindowSpaceFilter(nan, nan, nan)
        # TODO try some other eyetrackers providers? when they are implemented in icua2
        # pylint: disable=C0415
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
            # TODO we need to convert this to svg space!
            return EyeMotionEvent(**data)

        return EyetrackerWithUI(eyetracker_base, _eyemotioneventfactory, nan, nan, nan)
