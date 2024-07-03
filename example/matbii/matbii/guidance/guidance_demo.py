from star_ray_xml import XMLState, XMLSensor

from .._const import (
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_TRACKING,
)
from .guidance_base import GuidanceAgentBase

from .guidance_actuator import GuidanceActuator


class GuidanceAgentDemo(GuidanceAgentBase):

    def __init__(
        self,
    ):
        super().__init__([], [])
        self._box_guidance_actuator: GuidanceActuator = self.add_component(
            GuidanceActuator()
        )

    def __initialise__(self, state: XMLState):
        # set up initialise guidance, this just draws a box around each task, the agent will later decide whether this box is visible to the user
        # for task in self._tasks:
        #     self._box_guidance_actuator.guidance_box_on_element(
        #         f"guidance_box_{task}",
        #         task,
        #         opacity=0,
        #     )
        self._guidance_sensor.sense_element(TASK_ID_TRACKING)
        self._guidance_sensor.sense_element(TASK_ID_SYSTEM_MONITORING)
        self._guidance_sensor.sense_element(TASK_ID_RESOURCE_MANAGEMENT)
        return super().__initialise__(state)

    def __cycle__(self):
        # try:
        super().__cycle__()
        self.demo_toggle_box_guidance_by_mouse()
        self.demo_show_arrow_by_mouse()
        # except Exception as e:
        #     import traceback

        #     traceback.print_exception(e)

    def demo_show_arrow_by_gaze(self):
        if self.current_eye_position:
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
        pass
        # if self.current_mouse_position:
        #     for task in self._tasks:
        #         # highlight the task if the mouse is over it, otherwise hide it
        #         if task in self.mouse_at_elements:
        #             self._box_guidance_actuator.show_guidance_box(
        #                 f"guidance_box_{task}"
        #             )
        #         else:
        #             self._box_guidance_actuator.hide_guidance_box(
        #                 f"guidance_box_{task}"
        #             )
