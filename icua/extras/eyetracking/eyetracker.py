from typing import List, Dict, Any, Callable, Tuple
from star_ray.event import Event, WindowMoveEvent, WindowResizeEvent
from .eyetrackerbase import EyetrackerBase
from .filter import WindowSpaceFilter


class Eyetracker:

    def __init__(
        self,
        eyetracker_base: EyetrackerBase,
        event_factory: Callable[[Dict[str, Any]], Event],
    ):
        super().__init__()
        self._eyetracker_base = eyetracker_base
        self._event_factory = event_factory

    def get_nowait(self) -> List[Event]:
        events = self._eyetracker_base.get_nowait()
        events = [self._event_factory(event) for event in events]
        return events

    async def get(self) -> List[Event]:
        events = await self._eyetracker_base.get()
        events = [self._event_factory(event) for event in events]
        return events

    def get_filters(self):
        return self._eyetracker_base.get_filters() + [self._event_factory]

    def start(self):
        return self._eyetracker_base.start()

    def stop(self):
        return self._eyetracker_base.stop()


class EyetrackerWithUI(Eyetracker):

    def __init__(
        self,
        eyetracker: EyetrackerBase,
        event_factory: Callable[[Dict[str, Any]], Event],
        window_position: Tuple[float, float],
        window_size: Tuple[float, float],
        screen_size: Tuple[float, float],
    ):
        filters = eyetracker.get_filters()
        # locate the window space filter, or create it if it doesnt exist.
        # this filter is requried since we are working with a ui window.
        window_space_filter = list(
            filter(lambda f: isinstance(f, WindowSpaceFilter), filters)
        )
        if len(window_space_filter) == 0:
            raise ValueError(f"Missing required filter: {WindowSpaceFilter}")
        self._window_space_filter = window_space_filter[0]
        super().__init__(eyetracker, event_factory)

        # set the values of the filter.
        # NOTE: these values must be updated when/if the UI changes, otherwise this filter is meaningless
        # this can be done using the callbacks `on_window_move_event`, `on_window_resize_event`

        self.window_position = window_position
        self.window_size = window_size
        self.screen_size = screen_size
        assert self._window_space_filter in self._eyetracker_base.get_filters()

    def on_window_move_event(self, event: WindowMoveEvent):
        self.window_position = event.position

    def on_window_resize_event(self, event: WindowResizeEvent):
        self.window_size = event.size

    @property
    def screen_size(self):
        return self._window_space_filter.screen_size

    @screen_size.setter
    def screen_size(self, value):  #
        # sanity check
        assert (
            self._window_space_filter in self._eyetracker_base.get_filters()
        )  # the required filter was removed...
        self._window_space_filter.screen_size = value

    @property
    def window_size(self):
        return self._window_space_filter.window_size

    @window_size.setter
    def window_size(self, value):
        # sanity check
        assert (
            self._window_space_filter in self._eyetracker_base.get_filters()
        )  # the required filter was removed...
        self._window_space_filter.window_size = value

    @property
    def window_position(self):
        return self._window_space_filter.window_position

    @window_position.setter
    def window_position(self, value):
        # sanity check
        assert (
            self._window_space_filter in self._eyetracker_base.get_filters()
        )  # the required filter was removed...
        self._window_space_filter.window_position = value
