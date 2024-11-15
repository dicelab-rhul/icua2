"""Module containing the abstract base class `GuidanceActuator` and some concrete implementations: `ArrowGuidanceActuator` and `BoxGuidanceActuator` both provide convenient attempt methods for display visual guidance to a user."""

from math import isfinite
from abc import abstractmethod
from typing import Literal, Any
from star_ray.agent import Agent, Actuator, attempt
from star_ray.event import Action
from ..utils import LOGGER
from ..event import (
    MouseMotionEvent,
    EyeMotionEvent,
    DrawArrowAction,
    DrawBoxOnElementAction,
    ShowElementAction,
    HideElementAction,
    ShowGuidance,
    HideGuidance,
)


class GuidanceActuator(Actuator):
    """Abstract base class for guidance actuators."""

    @abstractmethod
    def show_guidance(self, **kwargs):
        """An attempt method that will show guidance to a user."""

    @abstractmethod
    def hide_guidance(self, **kwargs):
        """An attempt method that will hide guidance from a user."""


class CounterFactualGuidanceActuator(GuidanceActuator):
    """A simple guidance actuator that makes no change to the UI, but will take `ShowGuidance` and `HideGuidance` actions. These actions may be logged an used to determine when an agent decided to show/hide guidance to the user."""

    @attempt()
    def show_guidance(self, task: str) -> list[Action]:  # noqa
        return ShowGuidance(task=task)

    @attempt()
    def hide_guidance(self, task: str) -> list[Action]:  # noqa
        return HideGuidance(task=task)


class BoxGuidanceActuator(GuidanceActuator):
    """A concrete implementation of `GuidanceActuator` that implements box guidance. The box bounds a given task element serving to highlight it to the user, typically the task will be one that is not in an acceptible state."""

    def __init__(
        self,
        box_stroke_color: str = "#ff0000",
        box_stroke_width: float = 4.0,
    ):
        """Constructor.

        Args:
            box_stroke_color (str, optional): color of the box. Defaults to "#ff0000".
            box_stroke_width (float, optional): width of the box outline. Defaults to 4.0.
        """
        super().__init__()
        self._box_stroke_color = box_stroke_color
        self._box_stroke_width = box_stroke_width
        self._guidance_box_id_template = "guidance_box_%s"
        # ids of each of the guidance boxes that have been created
        # TODO they should be removed when `on_remove` is called!
        self._guidance_boxes = set()

    def on_remove(self, agent: Agent) -> None:  # noqa
        return super().on_remove(agent)  # TODO remove all guidance boxes!

    @attempt()
    def draw_guidance_box_on_element(
        self, element_id: str, **box_data: dict[str, Any]
    ) -> DrawBoxOnElementAction:
        """Attempt method that will draw a box around a given element.

        Args:
            element_id (str): the `id` of the element.
            box_data (dict[str,Any]): data associated with the box.

        Returns:
            DrawBoxOnElementAction: action
        """
        # TODO explicit parameters for box data
        box_data["id"] = self._guidance_box_id_template % element_id
        return DrawBoxOnElementAction(
            xpath=f"//*[@id='{element_id}']", box_data=box_data
        )

    @attempt()
    def show_guidance(self, task: str) -> list[Action]:
        """Show guidance on the given task.

        Args:
            task (str): task to show guidance for.

        Returns:
            list[Action]: guidance actions
        """
        self._guidance_on = task
        guidance_box_id = self._guidance_box_id_template % task

        actions = []

        if guidance_box_id not in self._guidance_boxes:
            # first time! insert the guidance box
            self._guidance_boxes.add(guidance_box_id)
            box_data = {
                "stroke-width": self._box_stroke_width,
                "stroke": self._box_stroke_color,
            }
            # draw the box but it is hidden (opacity=0)
            actions.append(
                self.draw_guidance_box_on_element(task, opacity=0.0, **box_data)
            )
        actions.append(ShowElementAction(xpath=f"//*[@id='{guidance_box_id}']"))
        return actions

    @attempt()
    def hide_guidance(self, task: str):
        """Hide guidance on the given task.

        Args:
            task (str): task to hide guidance for.

        Returns:
            list[Action]: guidance actions
        """
        self._guidance_on = None
        guidance_box_id = self._guidance_box_id_template % task

        actions = []

        if guidance_box_id not in self._guidance_boxes:
            # first time! insert the guidance box
            self._guidance_boxes.add(guidance_box_id)
            box_data = {
                "stroke-width": self._box_stroke_width,
                "stroke": self._box_stroke_color,
            }
            # draw the box but it is hidden (opacity=0)
            actions.append(
                self.draw_guidance_box_on_element(task, opacity=0.0, **box_data)
            )
        actions.append(HideElementAction(xpath=f"//*[@id='{guidance_box_id}']"))
        return actions


class ArrowGuidanceActuator(GuidanceActuator):
    """A concrete implementation of `GuidanceActuator` that implements a guidance arrow.

    The arrow can be displayed in three different ways depending on the value of `arrow_mode`:
    - "gaze" will display the arrow at the users gaze position, offset by `arrow_offset`.
    - "mouse" will display the arrow at the users mouse position, offset by `arrow_offset`.
    - "fixed" will display the arrow at a fixed position on the screen, this position is specified by `arrow_offset`.
    """

    ARROW_MODES = Literal["gaze", "mouse", "fixed"]

    def __init__(
        self,
        arrow_mode: Literal["gaze", "mouse", "fixed"],
        arrow_scale: float = 1.0,
        arrow_fill_color: str = "none",
        arrow_stroke_color: str = "#ff0000",
        arrow_stroke_width: float = 4.0,
        arrow_offset: tuple[float, float] = (80, 80),
    ):
        """Constructor.

        Args:
            arrow_mode (Literal["gaze", "mouse", "fixed"]): modes for arrow display.
            arrow_scale (float, optional): scale of the arrow. Defaults to 1.0.
            arrow_fill_color (str, optional): fill colour of the arrow. Defaults to "none".
            arrow_stroke_color (str, optional): line colour of the arrow outline. Defaults to "#ff0000".
            arrow_stroke_width (float, optional): line width of the arrow outline. Defaults to 4.0.
            arrow_offset (tuple[float, float], optional): offset of the arrow from its set position. This is the position used if `arrow_mode == "fixed". Defaults to (80, 80).
        """
        super().__init__()
        self._arrow_mode = arrow_mode
        self._arrow_scale = arrow_scale
        self._arrow_fill_color = arrow_fill_color
        self._arrow_stroke_color = arrow_stroke_color
        self._arrow_stroke_width = arrow_stroke_width
        self._arrow_offset = arrow_offset

        if self._arrow_mode not in ArrowGuidanceActuator.ARROW_MODES.__args__:
            raise ValueError(
                f"Invalid argument: `arrow_mode` must be one of {ArrowGuidanceActuator.ARROW_MODES}"
            )
        self._guidance_arrow_id = "guidance_arrow"
        self._guidance_on = None
        self._gaze_position = None
        self._mouse_position = None

    def __attempt__(self):  # noqa
        if self._guidance_on is None:
            return []
        elif self._arrow_mode == "gaze":
            # eyetracking positions can be nan, dont update the position if they are?
            if isfinite(self._gaze_position[0]) and isfinite(self._gaze_position[1]):
                attrs = dict(
                    id=self._guidance_arrow_id,
                    x=self._gaze_position[0] + self._arrow_offset[0],
                    y=self._gaze_position[1] + self._arrow_offset[0],
                    point_to=self._guidance_on,
                )
                return [DrawArrowAction(xpath="/svg:svg", data=attrs)]
            else:
                LOGGER.warning("Ignoring NaN arrow position.")
            return []
        elif self._arrow_mode == "mouse":
            if self._mouse_position:
                attrs = dict(
                    id=self._guidance_arrow_id,
                    x=self._mouse_position[0] + self._arrow_offset[0],
                    y=self._mouse_position[1] + self._arrow_offset[0],
                    point_to=self._guidance_on,
                )
                return [DrawArrowAction(xpath="/svg:svg", data=attrs)]
            return []
        elif self._arrow_mode == "fixed":
            # TODO where should it be? the center of the screen?
            raise NotImplementedError("TODO")
        else:
            raise ValueError(
                f"Invalid argument: `arrow_mode` must be one of {ArrowGuidanceActuator.ARROW_MODES}"
            )

    @attempt([EyeMotionEvent])
    def set_gaze_position(self, action: EyeMotionEvent) -> None:
        """Sets the users current gaze position. This may be used as a position for arrow display."""
        self._gaze_position = action.position

    @attempt([MouseMotionEvent])
    def set_mouse_motion(self, action: MouseMotionEvent) -> None:
        """Sets the users current mouse position. This may be used as a position for arrow display."""
        self._mouse_position = action.position

    def on_add(self, agent: Agent) -> None:  # noqa
        super().on_add(agent)
        self.draw_guidance_arrow(
            self._guidance_arrow_id,
            0.0,
            0.0,
            fill=self._arrow_fill_color,
            stroke_width=self._arrow_stroke_width,
            stroke_color=self._arrow_stroke_color,
            opacity=0.0,
            scale=self._arrow_scale,
        )

    def on_remove(self, agent: Agent) -> None:  # noqa
        super().on_remove(agent)
        # TODO remove arrow element!

    @attempt()
    def draw_guidance_arrow(
        self,
        name: str,
        x: float,
        y: float,
        scale: float = 1.0,
        rotation: float = 0.0,
        fill: str = "none",
        opacity: float = 0.0,
        stroke_color: str = "#ff0000",
        stroke_width: float = 2.0,
        **kwargs,
    ) -> DrawArrowAction:
        """Attempt method that takes an action to draw a guidance arrow.

        Args:
            name (str): id.
            x (float): x position.
            y (float): y position.
            scale (float, optional): scale. Defaults to 1.0.
            rotation (float, optional): rotation. Defaults to 0.0.
            fill (str, optional): fill color. Defaults to "none".
            opacity (float, optional): opacity (0.0 means hidden). Defaults to 0.0.
            stroke_color (str, optional): color of the arrow border. Defaults to "#ff0000".
            stroke_width (float, optional): thickness of the arrow border. Defaults to 2.0.
            kwargs : (dict[str,Any]): additional optional keyword arguments.

        Returns:
            DrawArrowAction: action
        """
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
                stroke=stroke_color,
                stroke_width=stroke_width,
                **kwargs,
            ),
        )

    @attempt()
    def show_guidance(self, task: str) -> list[Action]:
        """Show guidance on the given task.

        Args:
            task (str): task to show guidance for.

        Returns:
            list[Action]: guidance actions
        """
        self._guidance_on = task
        actions = [
            ShowElementAction(xpath=f"//*[@id='{self._guidance_arrow_id}']"),
        ]
        return actions

    @attempt()
    def hide_guidance(self, task: str) -> list[Action]:
        """Hide guidance on the given task.

        Args:
            task (str): task to hide guidance for.

        Returns:
            list[Action]: guidance actions
        """
        self._guidance_on = None
        actions = [
            HideElementAction(xpath=f"//*[@id='{self._guidance_arrow_id}']"),
        ]
        return actions
