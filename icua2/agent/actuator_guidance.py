from abc import ABC, abstractmethod
from typing import List, Tuple
from star_ray.agent import Actuator, attempt
from icua2.event import MouseMotionEvent, EyeMotionEvent, WindowResizeEvent, Update
from .action_guidance import (
    DrawArrowAction,
    DrawBoxOnElementAction,
    ShowElementAction,
    HideElementAction,
    ShowGuidance,
    HideGuidance
)
import math
import time


class GuidanceActuator(ABC, Actuator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def __initialise__(self, **kwargs):
        pass

    @abstractmethod
    def show_guidance(self, **kwargs):
        pass

    @abstractmethod
    def hide_guidance(self, **kwargs):
        pass


class DefaultGuidanceActuator(GuidanceActuator):

    ARROW_MODES = ("gaze", "mouse", "fixed", "none")

    def __init__(self, *args, arrow_mode: str = "gaze",
                 arrow_scale: float = 1.0,
                 arrow_fill_color: str = "none",
                 arrow_stroke_color: str = "#ff0000",
                 arrow_stroke_width: float = 4.0,
                 arrow_offset: Tuple[float, float] = (80, 80),
                 box_stroke_color: str = "#ff0000",
                 box_stroke_width: float = 4.0,

                 **kwargs):
        super().__init__(*args, **kwargs)
        self._arrow_mode = arrow_mode
        self._arrow_scale = arrow_scale
        self._arrow_fill_color = arrow_fill_color
        self._arrow_stroke_color = arrow_stroke_color
        self._arrow_stroke_width = arrow_stroke_width
        self._arrow_offset = arrow_offset
        self._box_stroke_color = box_stroke_color
        self._box_stroke_width = box_stroke_width

        if not self._arrow_mode in DefaultGuidanceActuator.ARROW_MODES:
            raise ValueError(
                f"Invalid argument: `arrow_mode` must be one of {DefaultGuidanceActuator.ARROW_MODES}")
        self._guidance_arrow_id = "guidance_arrow"
        self._guidance_box_id_template = "guidance_box_%s"
        self._guidance_on = None
        self._gaze_position = None
        self._mouse_position = None

    def __attempt__(self):
        if self._guidance_on is None:
            return []
        if self._arrow_mode == "none":
            return []
        elif self._arrow_mode == "gaze":
            if self._gaze_position:  # TODO check that this doesnt continuously hold...?
                attrs = dict(id=self._guidance_arrow_id,
                             x=self._gaze_position[0] + self._arrow_offset[0],
                             y=self._gaze_position[1] + self._arrow_offset[0],
                             point_to=self._guidance_on)
                return [DrawArrowAction(xpath="/svg:svg", data=attrs)]
            return []
        elif self._arrow_mode == "mouse":
            if self._mouse_position:
                attrs = dict(id=self._guidance_arrow_id,
                             x=self._mouse_position[0] + self._arrow_offset[0],
                             y=self._mouse_position[1] + self._arrow_offset[0],
                             point_to=self._guidance_on)
                return [DrawArrowAction(xpath="/svg:svg", data=attrs)]
            return []
        elif self._arrow_mode == "fixed":
            # TODO where should it be? the center of the screen?
            raise NotImplementedError("TODO")
        else:
            raise ValueError(
                f"Invalid argument: `arrow_mode` must be one of {DefaultGuidanceActuator.ARROW_MODES}")

    @property
    def is_arrow_mode_none(self) -> bool:
        return self._arrow_mode == "none"

    @attempt([EyeMotionEvent])
    def get_gaze_position(self, action: EyeMotionEvent):
        self._gaze_position = action.position

    @attempt([MouseMotionEvent])
    def get_mouse_motion(self, action: MouseMotionEvent):
        self._mouse_position = action.position

    def __initialise__(self, tasks: List[str] = None, **kwargs):
        assert tasks is not None  # requires argument `tasks`
        if not self.is_arrow_mode_none:
            self.draw_guidance_arrow(
                self._guidance_arrow_id, 0.0, 0.0,
                fill=self._arrow_fill_color,
                stroke_width=self._arrow_stroke_width,
                stroke_color=self._arrow_stroke_color,
                opacity=0.0,
                scale=self._arrow_scale)
        for task in tasks:
            box_data = {"stroke-width": self._box_stroke_width,
                        "stroke": self._box_stroke_color}
            self.draw_guidance_box_on_element(task, opacity=0.0, **box_data)

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
        ** kwargs,
    ) -> DrawArrowAction:
        if self.is_arrow_mode_none:
            raise ValueError(
                "Attempting to draw guidance arrow when `arrow_mode` == 'none'")
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
    def draw_guidance_box_on_element(self, task: str, **kwargs) -> DrawBoxOnElementAction:
        kwargs['id'] = self._guidance_box_id_template % task
        return DrawBoxOnElementAction(xpath=f"//*[@id='{task}']", box_data=kwargs)

    @attempt()
    def show_guidance(self, task: str = None, **kwargs):
        assert task  # requires argument `task`
        self._guidance_on = task
        guidance_box_id = self._guidance_box_id_template % task
        actions = [ShowGuidance(task=task),
                   ShowElementAction(xpath=f"//*[@id='{guidance_box_id}']")]
        if not self.is_arrow_mode_none:
            actions.append(ShowElementAction(
                xpath=f"//*[@id='{self._guidance_arrow_id}']"))
        return actions

    @attempt()
    def hide_guidance(self, task: str = None, **kwargs):
        assert task  # requires argument `task`
        self._guidance_on = None
        guidance_box_id = self._guidance_box_id_template % task
        actions = [HideGuidance(task=task),
                   HideElementAction(xpath=f"//*[@id='{guidance_box_id}']")]
        if not self.is_arrow_mode_none:
            actions.append(HideElementAction(
                xpath=f"//*[@id='{self._guidance_arrow_id}']"))
        return actions


# def initialise_guidance_box(
#         self, name: str, x: float, y: float, width: float, height: float, **kwargs
#     ):
#         assert (name and x and y and width and height) is not None
#         return DrawBoxAction(
#             xpath="/svg:svg",
#             box_data=dict(
#                 id=name,
#                 x=x,
#                 y=y,
#                 width=width,
#                 height=height,
#                 **kwargs,
#             ),
#         )
