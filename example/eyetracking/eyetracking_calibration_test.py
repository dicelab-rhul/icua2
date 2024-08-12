from typing import Any
from random import uniform

from star_ray_pygame import SVGAmbient, Environment, AvatarActuator, WindowConfiguration
from star_ray_pygame.event import MouseMotionEvent, Insert, Update
from star_ray import attempt
from star_ray.utils import _LOGGER

from icua.agent import Avatar
from icua.extras.eyetracking.tobii import TobiiEyetracker


from icua.utils import LOGGER

from icua.extras.eyetracking import EyeMotionEventRaw, EyeMotionEvent, EyetrackerIOSensor




LOGGER.set_level("INFO")
_LOGGER.setLevel("WARNING")


class FollowActuator(AvatarActuator):

    CIRCLE = """<svg:circle id="{id}" cx="0" cy="0" r="{radius}" fill="{color}" stroke="black" stroke-width="2" xmlns:svg="http://www.w3.org/2000/svg"/>"""

    def on_add(self, agent: Avatar) -> None:
        super().on_add(agent)
        self.insert_circles()

    @attempt
    def insert_circles(self):
        """Inserts circle elements which will follow the mouse."""
        circle1 = FollowActuator.CIRCLE.format(
            id="circle-1", color="yellow", radius="40"
        )
        circle2 = FollowActuator.CIRCLE.format(
            id="circle-2", color="red", radius="40"
        )
        return [
            Insert.new("/svg:svg", circle1, index=1),
            Insert.new("/svg:svg", circle2, index=2),
        ]
    
    @attempt()
    def update(self, id: str, position : tuple[float,float]):
        return Update.new(
            xpath=f"/svg:svg/svg:circle[@id='{id}']",
            attrs={"cx": position[0], "cy": position[1]},
        )
    
    @attempt()
    def show(self, id: str, show: bool = True):
        return Update.new(
            xpath=f"/svg:svg/svg:circle[@id='{id}']",
            attrs={"opacity": float(show)},
        )

    @attempt()
    def on_mouse_motion(self, event: MouseMotionEvent):  # noqa: D102
        return self.update("circle-1",event.position)

    @attempt()
    def on_gaze_motion(self, event : EyeMotionEvent):
        return self.update("circle-2", event.position)
    
if __name__ == "__main__":
    class Stub:
        def get_nowait(self):
            return [EyeMotionEventRaw(position=(0.1,0.1))]
    eyetracker = TobiiEyetracker(uri="tet-tcp://172.28.195.1")
    
    #eyetracker = Stub()
    
    window_config = WindowConfiguration(width=1200, height=800)
    eyetracker_sensor = EyetrackerIOSensor(eyetracker)

    avatar = Avatar(
        [eyetracker_sensor], [FollowActuator()], window_config=window_config
    )
    ambient = SVGAmbient([avatar])
    env = Environment(ambient, wait=0.05)
    env.run()
