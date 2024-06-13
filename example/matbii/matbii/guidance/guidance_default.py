from typing import Dict, Any
from pydantic import validator
import lxml.etree as etree
from star_ray.agent import Actuator, attempt
from star_ray.agent.component.component import Component
from star_ray.event import Action
from star_ray.event.observation_event import ErrorObservation
from star_ray_xml import XMLState, insert, update, select
from icua2.utils import DEFAULT_XML_NAMESPACES


from .action import *

from .._const import (
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_TRACKING,
)
from .guidance_base import GuidanceAgentBase


class BoxGuidanceActuator(Actuator):

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


class GuidanceAgentDefault(GuidanceAgentBase):

    def __init__(self):
        super().__init__()
        self._box_guidance_actuator: BoxGuidanceActuator = self.add_component(
            BoxGuidanceActuator()
        )
        self._guidance_initialised = False
        self._tasks = set(
            [
                TASK_ID_RESOURCE_MANAGEMENT,
                TASK_ID_SYSTEM_MONITORING,
                TASK_ID_TRACKING,
            ]
        )

    def __initialise__(self, state: XMLState):
        # set up initialise guidance, this just draws a box around each task, the agent will later decide whether this box is visible to the user
        for task in self._tasks:
            self._box_guidance_actuator.guidance_box_on_element(
                f"guidance_box_{task}",
                task,
                opacity=0,
            )
        return super().__initialise__(state)

    def __cycle__(self):
        super().__cycle__()  # update beliefs
        self.demo_toggle_box_guidance_by_mouse()
        self.demo_show_arrow_by_gaze()

    def demo_show_arrow_by_gaze(self):
        if self.current_eye_position:
            # print(self.current_eye_position)
            self._box_guidance_actuator.guidance_arrow(
                "guidance_arrow", *self.current_eye_position["position"]
            )

    def demo_show_arrow_by_mouse(self):
        if self.current_mouse_position:
            self._box_guidance_actuator.guidance_arrow(
                "guidance_arrow", *self.current_mouse_position["position"]
            )

    def demo_show_box_at_mouse(self):
        if self.current_mouse_position:
            self._box_guidance_actuator.guidance_box(
                "guidance_box_test", *self.current_mouse_position["position"], 10, 10
            )

    def demo_toggle_box_guidance_by_mouse(self):
        if self.current_mouse_position:
            for task in self._tasks:
                # highlight the task if the mouse is over it, otherwise hide it
                if task in self.mouse_at_elements:
                    self._box_guidance_actuator.show_guidance_box(
                        f"guidance_box_{task}"
                    )
                else:
                    self._box_guidance_actuator.hide_guidance_box(
                        f"guidance_box_{task}"
                    )
