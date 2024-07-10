import asyncio
from star_ray_pygame import View, WindowConfiguration

from star_ray.agent import Actuator, attempt
from star_ray_xml import Update
from matbii.agent.avatar import Avatar, PygameAvatar
from star_ray_xml import XMLAmbient
from star_ray.environment import _Ambient
from icua2.extras.eyetracking import EyeMotionEvent


class EyeFollow(Actuator):

    @attempt
    def attempt(self, event: EyeMotionEvent):
        cx, cy = event.position
        action = Update(xpath="//*[@id='mycircle']", attrs=dict(cx=cx, cy=cy))
        return [action]


async def main(
    task_name="eye_tracking",
    x=0,
    y=0,
    width=1000,
    height=1000,
    cx=480 / 2 - 5,
    cy=480 / 2 - 5,
    radius=10,
    stroke_color="#ff0000",
    stroke=2,
    color="#ff0000",
):

    # -------------------- #
    window_config = WindowConfiguration(
        width=1000, height=480, title="svg test", resizable=True, fullscreen=False
    )
    # avatar = PygameAvatar([], [], window_config=window_config)
    avatar = PygameAvatar(
        [],
        [EyeFollow()],
        window_config=window_config,
        eyetracker=Avatar.get_default_eyetracker(),
    )
    state = XMLAmbient(
        [avatar],
        f"""<svg:svg id="{task_name}" xmlns:svg="http://www.w3.org/2000/svg" x="{x}" y="{y}" width="{width}"
    height="{height}">
    
    <svg:circle id="mycircle" cx="{cx}" cy="{cy}" r="{radius}" stroke="{stroke_color}" stroke-width="{stroke}"
        fill="{color}" />
    </svg:svg>""",
    )
    state = _Ambient.new(state)
    avatar = state.get_agents()[0]
    await state.__initialise__()
    await avatar.__initialise__(state)
    while True:
        await avatar.__sense__(state)
        await avatar.__cycle__()
        await avatar.__execute__(state)
        await asyncio.sleep(0.1)


asyncio.run(main())
