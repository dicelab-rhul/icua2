from logging import INFO
from typing import List
from star_ray.agent import attempt, Actuator
from star_ray.utils import TypeRouter

from star_ray.environment import State
from star_ray_pygame.utils import LOGGER
from star_ray_pygame import SVGAmbient, Environment, Avatar
from star_ray_pygame.actuator import AvatarActuator
from star_ray_pygame.event import UserInputEvent, MouseButtonEvent
from star_ray_xml import Select, Update
from icua2.agent import (
    GuidanceAgent,
    TaskAcceptabilitySensor,
    DrawBoxAction,
    HideElementAction,
    ShowElementAction,
)
from icua2.extras.eyetracking import EyeMotionEvent


USER_INPUT_TYPES = TypeRouter.resolve_route_types(UserInputEvent)
USER_INPUT_TYPES.append(EyeMotionEvent)
LOGGER.setLevel(INFO)


TASK_NAME = "circle-task"
SVG = f"""
<svg:svg xmlns:svg="http://www.w3.org/2000/svg" width="200" height="200">
    <svg:circle id="{TASK_NAME}" cx="50" cy="50" r="40" stroke="black" stroke-width="2" fill="red"/>
</svg:svg>
"""


class CircleTaskSensor(TaskAcceptabilitySensor):
    COLOR_INACTIVE = "none"
    COLOR_ACCEPTABLE = "red"

    def is_acceptable(self, task: str = None, **kwargs) -> bool:
        color = self.beliefs[self.task_name].get("fill", "none")
        return color == CircleTaskSensor.COLOR_ACCEPTABLE

    def is_active(self, task: str = None, **kwargs) -> bool:
        color = self.beliefs[self.task_name].get("fill", "none")
        return color != CircleTaskSensor.COLOR_INACTIVE

    def sense(self) -> List[Select]:
        # for this task, we are keeping track of the circles fill
        return [
            self.sense_element(
                element_id=self.task_name, attributes=["fill", "r", "cx", "cy"]
            ),
            self.sense_element(
                element_id="circle-task-box-highlight",
                attributes=["x", "y", "width", "height"],
            ),
        ]


class CircleTaskActuator(Actuator):
    @attempt
    def color_swap(self, action: MouseButtonEvent):
        if action.status == MouseButtonEvent.DOWN:
            if action.button == MouseButtonEvent.BUTTON_LEFT:
                return Update(
                    xpath=f".//svg:circle[@id='{TASK_NAME}']", attrs={"fill": "blue"}
                )
            elif action.button == MouseButtonEvent.BUTTON_RIGHT:
                return Update(
                    xpath=f".//svg:circle[@id='{TASK_NAME}']", attrs={"fill": "red"}
                )
        return None

    @attempt([])
    def draw_box_highlight(self, x: float, y: float, width: float, height: float):
        xpath = f"/svg:svg"
        box_data = dict(
            id="circle-task-box-highlight",
            x=x,
            y=y,
            width=width,
            height=height,
            opacity=1.0,
        )
        return [DrawBoxAction(xpath=xpath, box_data=box_data)]

    @attempt([])
    def show_box_highlight(self):
        xpath = f".//svg:rect[@id='circle-task-box-highlight']"
        return [ShowElementAction(xpath=xpath)]

    @attempt([])
    def hide_box_highlight(self):
        xpath = f".//svg:rect[@id='circle-task-box-highlight']"
        return [HideElementAction(xpath=xpath)]


class CircleTaskGuidanceAgent(GuidanceAgent):
    def __init__(self):
        super().__init__(
            [CircleTaskSensor(TASK_NAME)],
            [CircleTaskActuator()],
            user_input_events=USER_INPUT_TYPES,
        )

    def circle_task_sensor(self) -> CircleTaskSensor:
        return next(filter(lambda x: isinstance(x, CircleTaskSensor), self.sensors))

    def circle_task_actuator(self) -> CircleTaskActuator:
        return next(filter(lambda x: isinstance(x, CircleTaskActuator), self.actuators))

    def on_acceptable(self, task: str):
        actuator: CircleTaskActuator = self.circle_task_actuator()
        actuator.hide_box_highlight()

    def on_unacceptable(self, task: str):
        actuator: CircleTaskActuator = self.circle_task_actuator()
        actuator.show_box_highlight()

    def on_active(self, task: str):
        # when the task becomes active
        actuator = self.circle_task_actuator()
        sensor = self.circle_task_sensor()
        beliefs = sensor.beliefs[TASK_NAME]
        cx, cy, r = beliefs["cx"], beliefs["cy"], beliefs["r"]
        x, y = cx - r, cy - r
        width, height = r * 2, r * 2
        actuator.draw_box_highlight(x, y, width, height)


guidance_agent = CircleTaskGuidanceAgent()

avatar = Avatar([], [CircleTaskActuator(), AvatarActuator()])
agents = [avatar, guidance_agent]
env = Environment(SVGAmbient(agents, svg=SVG))

env.run()
