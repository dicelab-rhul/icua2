from star_ray.agent import Actuator, attempt
from icua2.agent.guidance.action import (
    DrawArrowAction,
    DrawBoxAction,
    DrawBoxOnElementAction,
    ShowElementAction,
    HideElementAction,
)


class GuidanceActuator(Actuator):

    @attempt
    def guidance_arrow(
        self,
        name: str,
        x: float,
        y: float,
        scale: float = 1.0,
        rotation: float = 0,
        fill: str = "none",
        opacity: float = 1,
        stroke: float = 2,
        **kwargs,
    ):
        return DrawArrowAction(
            xpath="/svg:svg",
            data=dict(
                id=name,
                x=x,
                y=y,
                scale=scale,
                rotation=rotation,
                fill=fill,
                opacity=opacity,
                stroke=stroke,
                **kwargs,
            ),
        )

    @attempt
    def guidance_box(
        self, name: str, x: float, y: float, width: float, height: float, **kwargs
    ):
        assert (name and x and y and width and height) is not None
        return DrawBoxAction(
            xpath="/svg:svg",
            box_data=dict(
                id=name,
                x=x,
                y=y,
                width=width,
                height=height,
                **kwargs,
            ),
        )

    @attempt
    def guidance_box_on_element(self, name: str, element_id: str, **kwargs):
        kwargs.setdefault("id", name)
        return DrawBoxOnElementAction(xpath=f"//*[@id='{element_id}']", box_data=kwargs)

    @attempt
    def show_guidance_box(self, name: str):
        return ShowElementAction(xpath=f"//*[@id='{name}']")

    @attempt
    def hide_guidance_box(self, name):
        return HideElementAction(xpath=f"//*[@id='{name}']")
