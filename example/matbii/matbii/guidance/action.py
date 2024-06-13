from typing import Dict, Any, ClassVar, Tuple
from pydantic import validator
import copy
import lxml.etree as etree
from star_ray.event import Action
from star_ray_xml import XMLState, insert, update, select
from icua2.utils import DEFAULT_XML_NAMESPACES


__all__ = (
    "XPathAction",
    "DrawArrowAction",
    "DrawBoxAction",
    "DrawBoxOnElementAction",
    "ShowElementAction",
    "HideElementAction",
)


class XPathAction(Action):

    xpath: str

    @validator("xpath", pre=True, always=True)
    @classmethod
    def _validate_xpath(cls, xpath):
        if not isinstance(xpath, str) or xpath.endswith("/"):
            raise ValueError(f"Invalid xpath: '{xpath}'")
        return xpath


class DrawElementAction(XPathAction):

    data: Dict[str, str]
    REQUIRED_DATA: ClassVar[Tuple[str]] = tuple()

    @validator("data", pre=True, always=True)
    @classmethod
    def _validate_data(cls, data):
        data = DrawElementAction._validate_none_data(data)
        return DrawElementAction._validate_required_data(data)

    @classmethod
    def _validate_none_data(cls, data):
        def _validate(data):
            for k, v in data.items():
                if v is None:
                    raise ValueError(
                        f"{DrawBoxAction.__name__} attribute: {k} cannot be None"
                    )
                yield str(k), str(v)

        return dict(_validate(data))

    @classmethod
    def _validate_required_data(cls, data):
        if not all(x in data for x in cls.REQUIRED_DATA):
            missing = [x for x in cls.REQUIRED_DATA if not x in data]
            raise ValueError(
                f"{DrawBoxAction.__name__} is missing attributes: {missing}"
            )
        return data

    @classmethod
    def _insert(cls, state: XMLState, data: Dict[str, str], xpath: str):
        raise NotImplementedError()

    @classmethod
    def _update(cls, state: XMLState, data: Dict[str, str], xpath: str):
        raise NotImplementedError()

    @classmethod
    def _draw(cls, state: XMLState, data: Dict[str, str], xpath: str):
        raise NotImplementedError()

    def execute(self, state: XMLState):
        return type(self)._draw(state, self.data, self.xpath)


class DrawArrowAction(DrawElementAction):

    ARROW_SVG: ClassVar[str] = (
        """<svg:svg xmlns:svg="http://www.w3.org/2000/svg" transform="scale({scale})" id="{id}" x="{x}" y="{y}" viewBox="-28 -28 178 178" width="200" height="200"><svg:polygon transform="rotate({rotation}, 61.44, 61.44)" fill="{fill}" stroke="{stroke}" stroke-color="{stroke-color}" points="148.33, 61.44 32.07, 118.96 62.71, 61.44 32.07, 3.92 148.33, 61.44" /> </svg:svg>"""
    )
    REQUIRED_DATA: ClassVar[Tuple[str]] = ("id",)

    @classmethod
    def _insert(cls, state: XMLState, data: Dict[str, str], xpath: str):
        element = DrawArrowAction.ARROW_SVG.format(**data)
        return state.insert(insert(xpath, element, index=0))

    @classmethod
    def _set_if(cls, attr: str, element: etree.ElementBase, data: Dict[str, str]):
        if attr in data:
            element.set(attr, data[attr])

    @classmethod
    def _update(cls, state: XMLState, data: Dict[str, str], xpath: str):
        # update from data
        svg_data = {k: data[k] for k in ["scale", "x", "y"] if k in data}
        pol_data = {
            k: data[k]
            for k in ["rotation", "fill", "stroke", "stroke-color"]
            if k in data
        }
        pol_xpath = xpath + "/svg:polygon"
        state.update(update(xpath=xpath, attrs=svg_data))
        state.update(update(xpath=pol_xpath, attrs=pol_data))

    @classmethod
    def _draw(cls, state: XMLState, data: Dict[str, str], xpath: str):
        data.setdefault("fill", "none")
        data.setdefault("stroke", "2")
        data.setdefault("scale", "1")
        data.setdefault("rotation", "0")
        data.setdefault("stroke-color", "#ff0000")
        data.setdefault("x", "0")
        data.setdefault("y", "0")
        id = data.get("id", None)
        assert id is not None  # must have an 'id'
        # does the element already exist?
        uxpath = xpath + f"/svg:svg[@id='{data['id']}']"
        result = state.select(select(xpath=uxpath, attrs=["id"]))
        if result:
            # it already exists, update it
            cls._update(state, data, uxpath)
        else:
            # it doesnt exist, create it
            cls._insert(state, data, xpath)


class ShowElementAction(XPathAction):

    def execute(self, state: XMLState):
        return state.update(update(self.xpath, attrs={"opacity": 1}))


class HideElementAction(XPathAction):

    def execute(self, state: XMLState):
        return state.update(update(self.xpath, attrs={"opacity": 0}))


class DrawBoxAction(XPathAction):

    # TODO validate box_data, must contain x,y,width,height
    box_data: Dict[str, str]

    @validator("box_data", pre=True, always=True)
    @classmethod
    def _validate_box_data(cls, data):
        data = DrawBoxAction._validate_none_box_data(data)
        return DrawBoxAction._validate_required_box_data(data)

    @classmethod
    def _validate_none_box_data(cls, data):
        def _validate(data):
            for k, v in data.items():
                if v is None:
                    raise ValueError(
                        f"{DrawBoxAction.__name__} attribute: {k} cannot be None"
                    )
                yield str(k), str(v)

        return dict(_validate(data))

    @classmethod
    def _validate_required_box_data(cls, data: Dict[str, str]):
        if not all(x in data for x in ("x", "y", "width", "height")):
            missing = [x for x in ("x", "y", "width", "height") if not x in data]
            raise ValueError(
                f"{DrawBoxAction.__name__} is missing attributes: {missing}"
            )
        data.setdefault("stroke-width", "2")
        data.setdefault("stroke", "#ff0000")
        data.setdefault("fill", "none")
        return data

    @staticmethod
    def _new_box(state: XMLState, box_data: Dict[str, str], xpath: str):
        box = etree.Element(
            "{%s}rect" % DEFAULT_XML_NAMESPACES["svg"],
            attrib=box_data,
            nsmap=DEFAULT_XML_NAMESPACES,
        )
        box = etree.tostring(box)
        return state.insert(insert(xpath=xpath, element=box, index=0))

    @staticmethod
    def _draw_box(state: XMLState, box_data: Dict[str, str], xpath: str):
        box_id = box_data.get("id", None)
        if box_id is None:
            raise ValueError("Attempted to draw a box without an `id` attribute.")
        # check if the box already exists
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

    @validator("box_data", pre=True, always=True)
    @classmethod
    def _validate_box_data(cls, data):
        return DrawBoxAction._validate_none_box_data(data)

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
        try:
            result = DrawBoxAction._validate_none_box_data(result[0])
            box_data = {**self.box_data}
            box_data.update(result)
            box_data = DrawBoxAction._validate_required_box_data(box_data)
        except ValueError as e:
            raise ValueError(
                f"Failed to validate action {DrawBoxOnElementAction.__name__} for element at xpath: {self.xpath}"
            ) from e
        DrawBoxAction._draw_box(state, box_data, self.xpath + "/parent::*")
