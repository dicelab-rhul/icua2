"""Module defining guidance related events."""

from typing import ClassVar
from pydantic import field_validator
import lxml.etree as etree
import math

from star_ray.event import Action
from star_ray_xml import (
    XMLState,
    XPathQuery,
    insert,
    update,
    select,
    XPathElementsNotFound,
)
from star_ray_pygame.cairosurface import parse_transform
from star_ray_pygame import SVGAmbient


__all__ = (
    "TaskAcceptable",
    "TaskUnacceptable",
    "ShowGuidance",
    "HideGuidance",
    "XPathAction",
    "DrawArrowAction",
    "DrawBoxAction",
    "DrawBoxOnElementAction",
    "ShowElementAction",
    "HideElementAction",
)


class TaskAcceptable(Action):
    """This action to be taken when a task goes from an `acceptable` state to an `unacceptable` state."""

    task: str

    def __execute__(self, state: XMLState):  # noqa
        pass


class TaskUnacceptable(Action):
    """This action to be taken when a task goes from an `acceptable` state to an `unacceptable` state."""

    task: str

    def __execute__(self, state: XMLState):  # noqa
        pass


class ShowGuidance(Action):
    """This action should be taken when guidance starts being shown by an agent."""

    task: str

    def __execute__(self, state: XMLState):  # noqa
        pass


class HideGuidance(Action):
    """This action should be taken when guidance stops being shown by an agent."""

    task: str

    def __execute__(self, state: XMLState):  # noqa
        pass


class XPathAction(XPathQuery):
    """Base class for guidance actions, validates the xpath attribute of XPathQuery."""

    # @validator("xpath", pre=True, always=True)
    @field_validator("xpath", mode="before")
    @classmethod
    def _validate_xpath(cls, xpath):
        if not isinstance(xpath, str):
            raise TypeError(f"Invalid xpath: '{xpath}', must be of type `str`")
        if xpath.endswith("/"):
            xpath = xpath[:-1]
        return xpath

    @property
    def is_read(self):  # noqa: D102
        return False

    @property
    def is_write(self):  # noqa: D102
        return True

    @property
    def is_write_tree(self):  # noqa: D102
        return True  # possibly

    @property
    def is_write_element(self):  # noqa: D102
        return True


class DrawElementAction(XPathAction):
    data: dict[str, str]

    REQUIRED_DATA: ClassVar[tuple[str]] = tuple()

    # @validator("data", pre=True, always=True)
    @field_validator("data", mode="before")
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
                        f"{DrawBoxAction.__name__} attribute: {k} cannot be `None`."
                    )
                yield str(k), str(v)

        return dict(_validate(data))

    @classmethod
    def _validate_required_data(cls, data):
        if not all(x in data for x in cls.REQUIRED_DATA):
            missing = [x for x in cls.REQUIRED_DATA if x not in data]
            raise ValueError(
                f"{DrawBoxAction.__name__} is missing attributes: {missing}"
            )
        return data

    @classmethod
    def _insert(cls, state: XMLState, data: dict[str, str], xpath: str):
        raise NotImplementedError()

    @classmethod
    def _update(cls, state: XMLState, data: dict[str, str], xpath: str):
        raise NotImplementedError()

    @classmethod
    def _draw(cls, state: XMLState, data: dict[str, str], xpath: str):
        raise NotImplementedError()

    def __execute__(self, state: XMLState):
        return type(self)._draw(state, self.data, self.xpath)


class DrawArrowAction(DrawElementAction):
    """Event that will draw an arrow in the UI.

    Optional values: scale, id, x, y, opacity, rotation, fill, stroke, stroke_width.
    """

    ARROW_SVG: ClassVar[str] = (
        """<svg:svg xmlns:svg="http://www.w3.org/2000/svg" transform="scale({scale})" id="{id}" x="{x}" y="{y}" opacity="{opacity}" viewBox="-28 -28 178 178" width="200" height="200"><svg:polygon transform="rotate({rotation}, 61.44, 61.44)" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" points="148.33, 61.44 32.07, 118.96 62.71, 61.44 32.07, 3.92 148.33, 61.44" /> </svg:svg>"""
    )
    REQUIRED_DATA: ClassVar[tuple[str]] = ("id",)

    @classmethod
    def new_rotation(cls, rotation: float) -> str:
        """TODO this should be a utility method."""
        return f"rotate({rotation}, 61.44, 61.44)"

    @classmethod
    def new_scale(cls, scale: float) -> str:
        """TODO this should be a utility method."""
        return f"scale({scale})"

    @classmethod
    def _insert(cls, state: XMLState, data: dict[str, str], xpath: str):
        data.setdefault("fill", "none")
        data.setdefault("opacity", "1")
        data.setdefault("stroke", "#ff0000")
        data.setdefault("scale", "1")
        data.setdefault("rotation", "0")
        data.setdefault("stroke_width", "2.0")
        data.setdefault("x", "0")
        data.setdefault("y", "0")
        element = DrawArrowAction.ARROW_SVG.format(**data)
        return state.insert(insert(xpath, element, index=10))

    @classmethod
    def _set_if(cls, attr: str, element: etree.ElementBase, data: dict[str, str]):
        if attr in data:
            element.set(attr, data[attr])

    @classmethod
    def _update(cls, state: XMLState, data: dict[str, str], xpath: str):
        pol_data = {
            k.replace("_", "-"): data[k]
            for k in ("fill", "stroke", "stroke_width")
            if k in data
        }
        if "scale" in data:
            transform = DrawArrowAction.new_scale(data["scale"])
            state.update(update(xpath=xpath, attrs={"transform": "transform"}))

        # update x and y, using x and y as the center coordinates
        if "x" in data or "y" in data:
            x, y = data.get("x", None), data.get("y", None)
            size, _ = DrawArrowAction.get_size_scale(state, xpath)
            attrs = {k: data[k] for k in ("opacity",) if k in data}
            if x is not None:
                attrs["x"] = str(float(x) - size[0] / 2)
            if y is not None:
                attrs["y"] = str(float(y) - size[1] / 2)
            state.update(update(xpath=xpath, attrs=attrs))

        if "rotation" in data:
            pol_data["transform"] = DrawArrowAction.new_rotation(data["rotation"])
        pol_xpath = xpath + "/svg:polygon"
        state.update(update(xpath=pol_xpath, attrs=pol_data))

        # check if we need to update the arrow to point to a target
        point_to = data.get("point_to", None)
        if point_to:
            rotation = DrawArrowAction.rotation_from_point_to(state, point_to, xpath)
            transform = DrawArrowAction.new_rotation(rotation)
            state.update(update(xpath=pol_xpath, attrs={"transform": transform}))

    @classmethod
    def _draw(cls, state: XMLState, data: dict[str, str], xpath: str):
        _id = data.get("id", None)
        assert _id is not None  # must have an 'id'
        # does the element already exist?
        uxpath = xpath + f"/svg:svg[@id='{data['id']}']"
        try:
            state.select(select(xpath=uxpath, attrs=["id"]))
        except XPathElementsNotFound:
            # it doesnt exist, create it
            return cls._insert(state, data, xpath)
        # it already exists, update it
        cls._update(state, data, uxpath)

    @staticmethod
    def get_size_scale(state: XMLState, xpath: str):
        """TODO this should be a utility method."""
        result = state.select(
            select(xpath, attrs=["x", "y", "width", "height", "transform"])
        )
        if not result:
            raise ValueError(f"Element at xpath: {xpath} doesn't exist")
        values = result[0]
        scale, _, _ = parse_transform(values["transform"])
        return (values["width"] * scale[0], values["height"] * scale[1]), scale

    @staticmethod
    def get_element_center(state: XMLState, xpath: str):
        """TODO this should be a utility method."""
        result = state.select(
            select(xpath, attrs=["x", "y", "width", "height", "transform"])
        )
        if not result:
            raise ValueError(f"Element at xpath: {xpath} doesn't exist")
        values = result[0]
        x, y = (float(values["x"]), float(values["y"]))
        scale, _, _ = parse_transform(values["transform"])
        width, height = (values["width"] * scale[0], values["height"] * scale[1])
        return x + width / 2, y + height / 2

    @staticmethod
    def rotation_from_point_to(state: XMLState, element_id: str, xpath: str) -> float:
        """Computes a rotation that points from the center of the arrow to the center of the given element.

        Args:
            state (XMLState): state of the environment
            element_id (str): element to point to
            xpath (str): xpath of the arrow element.

        Returns:
            float: rotation
        """
        # TODO this should be a utility method somewhere that will compute the rotation between two elements given their xpaths!
        # get the center of the arrow
        (x1, y1) = DrawArrowAction.get_element_center(state, xpath)
        # get the center of the element with id `element_id`
        (x2, y2) = DrawArrowAction.get_element_center(
            state, f".//*[@id='{element_id}']"
        )
        # compute angle between points
        return math.degrees(math.atan2(y2 - y1, x2 - x1))


class ShowElementAction(XPathAction):
    """Action to show an element by setting its opacity to 1."""

    def __execute__(self, state: XMLState):  # noqa
        return state.update(update(self.xpath, attrs={"opacity": 1}))


class HideElementAction(XPathAction):
    """Action to hide an element by setting its opacity to 0."""

    def __execute__(self, state: XMLState):  # noqa
        return state.update(update(self.xpath, attrs={"opacity": 0}))


class DrawBoxAction(XPathAction):
    """TODO."""

    box_data: dict[str, str]

    # @validator("box_data", pre=True, always=True)
    @field_validator("box_data", mode="before")
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
    def _validate_required_box_data(cls, data: dict[str, str]):
        if not all(x in data for x in ("x", "y", "width", "height")):
            missing = [x for x in ("x", "y", "width", "height") if x not in data]
            raise ValueError(
                f"{DrawBoxAction.__name__} is missing attributes: {missing}"
            )
        return data

    @staticmethod
    def _new_box(state: XMLState, box_data: dict[str, str], xpath: str):
        box_data.setdefault("stroke-width", "2")
        box_data.setdefault("stroke", "#ff0000")
        box_data.setdefault("fill", "none")
        box = etree.Element(
            f"{{{SVGAmbient.DEFAULT_SVG_NAMESPACES['svg']}}}rect",
            attrib=box_data,
            nsmap=SVGAmbient.DEFAULT_SVG_NAMESPACES,
        )
        box = etree.tostring(box)
        return state.insert(insert(xpath=xpath, element=box, index=0))

    @staticmethod
    def _draw_box(state: XMLState, box_data: dict[str, str], xpath: str):
        box_id = box_data.get("id", None)
        if box_id is None:
            raise ValueError("Attempted to draw a box without an `id` attribute.")
        # check if the box already exists
        uxpath = xpath + f"/svg:rect[@id='{box_id}']"
        try:
            state.select(select(xpath=uxpath, attrs=["id"]))
        except XPathElementsNotFound:
            # create a new box (it doesnt exist yet)
            return DrawBoxAction._new_box(state, box_data, xpath)
        return state.update(update(xpath=uxpath, attrs=box_data))

    def __execute__(self, state: XMLState):  # noqa
        return DrawBoxAction._draw_box(state, self.box_data, self.xpath)


class DrawBoxOnElementAction(DrawBoxAction):
    """TODO."""

    # @validator("box_data", pre=True, always=True)
    @field_validator("box_data", mode="before")
    @classmethod
    def _validate_box_data(cls, data):
        return DrawBoxAction._validate_none_box_data(data)

    def __execute__(self, state: XMLState):  # noqa
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
