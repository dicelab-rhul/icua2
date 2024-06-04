from typing import Dict, Any
import lxml.etree as etree
from star_ray.agent import Actuator, attempt
from star_ray.event import Action
from star_ray_xml import XMLState, insert, update, select
from icua2.utils import DEFAULT_XML_NAMESPACES

from .._const import (
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_TRACKING,
)
from .guidance_base import GuidanceAgentBase


class DrawBoxAction(Action):

    xpath: str
    # TODO validate box_data, must contain x,y,width,height
    box_data: Dict[str, str]

    @staticmethod
    def _new_box(state: XMLState, box_data: Dict[str, str], xpath: str):
        box = etree.Element(
            "{%s}rect" % DEFAULT_XML_NAMESPACES["svg"],
            attrib=box_data,
            nsmap=DEFAULT_XML_NAMESPACES,
        )
        box = etree.tostring(box)
        print(xpath, box)
        return state.insert(insert(xpath=xpath, element=box, index=0))

    @staticmethod
    def _draw_box(state: XMLState, box_data: Dict[str, str], xpath: str):
        box_id = box_data.get("id", None)
        if box_id is None:
            raise ValueError("Attempted to draw a box without an `id` attribute.")
        # check if the box already exists
        assert not xpath.endswith("/")  # this would not be a valid xpath...
        uxpath = xpath + f"/svg:rect[@id='{box_id}']"
        result = state.select(select(xpath=uxpath, attrs=["id"]))
        if result:
            return state.update(update(xpath=uxpath, attrs=box_data))
        else:
            return DrawBoxAction._new_box(
                state, box_data, xpath
            )  # create a new box (it doesnt exist yet)

    def execute(self, state: XMLState):
        return DrawBoxAction._draw_box(state, self.box_data, self.xpath)


class DrawBoxOnElementAction(DrawBoxAction):

    def execute(self, state: XMLState):
        required_attrs = ("x", "y", "width", "height")
        result = state.select(select(xpath=self.xpath, attrs=required_attrs))
        if not result:
            raise ValueError(
                f"Failed to find element at xpath: {self.xpath} for box draw."
            )
        if len(result) > 1:
            raise ValueError(
                f"Found multiple elements at xpath: {self.xpath} for box draw."
            )
        box_data = {**self.box_data}
        result = dict(filter(lambda x: x[1] is not None, result[0].items()))
        box_data.update({str(k): str(v) for k, v in result.items()})
        if any(not key in box_data for key in required_attrs):
            missing = [key for key in required_attrs if key not in box_data]
            raise ValueError(f"Element is missing required attributes: {missing}")
        assert not self.xpath.endswith("/")  # this would not be a valid xpath...
        DrawBoxAction._draw_box(state, box_data, self.xpath + "/parent::*")


class ShowElementAction(Action):
    pass


class HideElementAction(Action):
    pass


class BoxGuidanceActuator(Actuator):

    def _set_default_box_attributes(self, kwargs):
        kwargs.setdefault("stroke-width", "2")
        kwargs.setdefault("stroke", "red")
        kwargs.setdefault("fill", "none")
        return {str(k): str(v) for k, v in kwargs.items()}

    @attempt
    def guidance_box(self, name, x, y, width, height, **kwargs):
        kwargs = self._set_default_box_attributes(kwargs)
        return DrawBoxAction(
            xpath="/svg:svg",
            box_data=dict(
                id=str(name),
                x=str(x),
                y=str(y),
                width=str(width),
                height=str(height),
                **kwargs,
            ),
        )

    @attempt
    def guidance_box_on_element(self, element_id: str, **kwargs):
        kwargs = self._set_default_box_attributes(kwargs)
        kwargs.setdefault("id", f"guidance_box_{element_id}")
        return DrawBoxOnElementAction(xpath=f"//*[@id='{element_id}']", box_data=kwargs)

    @attempt
    def show_guidance_box(self, name):
        pass
        # return DrawBoxAction(
        #     xpath="/svg:svg",
        #     box_data={"id": name, "opacity": "1", "stroke-opacity": "1"},
        # )

    @attempt
    def hide_guidance_box(self, name):
        pass
        # return DrawBoxAction(
        #     xpath="/svg:svg",
        #     box_data={"id": name, "opacity": "0", "stroke-opacity": "0"},
        # )


class GuidanceAgentDefault(GuidanceAgentBase):

    def __init__(self):
        super().__init__()
        self._box_guidance_actuator: BoxGuidanceActuator = self.add_component(
            BoxGuidanceActuator()
        )

    def __cycle__(self):
        super().__cycle__()  # update beliefs
        # decide whether to give guidance
        # print(self.current_mouse_position)
        if self.current_mouse_position:
            self._box_guidance_actuator.guidance_box(
                "test", *self.current_mouse_position["position"], 50, 50
            )
            self._box_guidance_actuator.guidance_box_on_element(
                TASK_ID_RESOURCE_MANAGEMENT
            )
