from typing import Any
from random import uniform

from star_ray_pygame import SVGAmbient, Environment, Avatar, AvatarActuator
from star_ray_pygame.event import MouseMotionEvent, Insert, Update
from star_ray import attempt
from star_ray.utils import _LOGGER

from icua.extras.eyetracking import IVTFilter, WindowSpaceFilter, NWMAFilter


_LOGGER.setLevel("WARNING")


class MouseFollowActuator(AvatarActuator):
    """Actuator that moves the mouse making use of eyetracking filters allowing debuging and parameter choosing."""

    CIRCLE = """<svg:circle id="{id}" cx="0" cy="0" r="{radius}" fill="{color}" stroke="black" stroke-width="2" xmlns:svg="http://www.w3.org/2000/svg"/>"""
    BACKGROUND = """<svg:rect id="background" x="0" y="0" width="1000" height="1000" fill="yellow" xmlns:svg="http://www.w3.org/2000/svg"/>"""

    def __init__(
        self, velocity_threshold: float = 0.1, n: int = 10, noise_level: float = 0.05
    ):
        super().__init__()
        self.noise_level = noise_level
        self._ivt_filter = IVTFilter(velocity_threshold)
        self._ma_filter = NWMAFilter(n)
        # these will be set later
        na = tuple([float("nan"), float("nan")])
        self._window_space_filter = WindowSpaceFilter(na, na, na)
        self.screen_size = None
        self.window_size = None
        self.window_position = None

    @property
    def avatar(self) -> Avatar:
        return self._agent

    def _pixel_to_svg(self, point: tuple[float, float]):
        # convert pixel point to svg point
        return self.avatar._view.pixel_to_svg(point)

    def on_add(self, agent: Avatar) -> None:
        super().on_add(agent)
        self.screen_size = agent.get_screen_info()["size"]
        window_info = agent.get_window_info()
        self.window_size = window_info["size"]
        self.window_position = window_info["position"]
        self._window_space_filter.screen_size = self.screen_size
        self._window_space_filter.window_position = self.window_position
        self._window_space_filter.window_size = self.window_size
        self.insert_circles()

    def window_position_to_normalised_screen_position(
        self, position: tuple[float, float]
    ):
        """Convert window position to 0-1 screen position."""
        position = list(position)
        position[0] += self.window_position[0]
        position[1] += self.window_position[1]
        position[0] /= self.screen_size[0]
        position[1] /= self.screen_size[1]
        return tuple(position)

    @attempt
    def insert_circles(self):
        """Inserts circle elements which will follow the mouse."""
        circle = MouseFollowActuator.CIRCLE.format(
            id="circle", color="yellow", radius="40"
        )
        circle_random = MouseFollowActuator.CIRCLE.format(
            id="circle_rand", color="red", radius="10"
        )
        circle_smooth = MouseFollowActuator.CIRCLE.format(
            id="circle_smooth", color="green", radius="20"
        )
        return [
            # Insert.new("/svg:svg", MouseFollowActuator.BACKGROUND, 0),
            Insert.new("/svg:svg", circle, index=1),
            Insert.new("/svg:svg", circle_smooth, index=2),
            Insert.new("/svg:svg", circle_random, index=3),
        ]

    @attempt
    def on_mouse_motion(self, event: MouseMotionEvent):  # noqa: D102
        def _update_action(id: str, data: dict[str, Any]):
            position = self._pixel_to_svg(data["position"])
            return Update.new(
                xpath=f"/svg:svg/svg:circle[@id='{id}']",
                attrs={"cx": position[0], "cy": position[1]},
            )

        def _show_action(id: str, show: bool = True):
            return Update.new(
                xpath=f"/svg:svg/svg:circle[@id='{id}']",
                attrs={"opacity": float(show)},
            )

        actions = []
        # first we will convert the event to (0-1) screen coordinates to simulate an eyetracking coordinate.
        nsp = list(
            self.window_position_to_normalised_screen_position(event.position_raw)
        )

        # does the ivt filter work correctly? it should show/hide the yellow circle depending on fixate/saccade
        # the velocity threshold needs to be well chosen!
        data = self._ivt_filter(dict(position=nsp, timestamp=event.timestamp))
        # does the window space filter work correctly? it should convert 0-1 screen space to the window space
        # the yellow circle should follow the mouse pointer
        data = self._window_space_filter(data)
        actions.append(_update_action("circle", data))
        actions.append(_show_action("circle", show=data["fixated"]))

        # add some randomness
        nsp[0] += uniform(-self.noise_level, self.noise_level)
        nsp[1] += uniform(-self.noise_level, self.noise_level)

        # data = self._window_space_filter(dict(position=nsp))
        # actions.append(_update_action("circle_rand", data))
        # data = self._ma_filter(data)
        # actions.append(_update_action("circle_smooth", data))

        # add some noise to the new position
        # nsp[0] random.uniform(nsp) * self.noise_level
        # introduce
        return actions


if __name__ == "__main__":
    avatar = Avatar(
        [], [MouseFollowActuator(velocity_threshold=0.2, n=5, noise_level=0.05)]
    )
    ambient = SVGAmbient([avatar])
    env = Environment(ambient, wait=0.01)
    env.run()
