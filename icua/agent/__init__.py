"""Agent related functionality, including base classes for agents, actuators and sensors. Also contains some useful guidance related functionality, including some action definitions and `TaskAcceptabilitySensor`."""

from ..utils._task_loader import (
    agent_actuator,
    avatar_actuator,
)

from star_ray.agent import (
    Sensor,
    Actuator,
    Agent,
    attempt,
    observe,
)

from ..event.event_guidance import (
    ShowElementAction,
    HideElementAction,
    DrawArrowAction,
    DrawBoxAction,
    DrawBoxOnElementAction,
    DrawElementAction,
)
from .acceptability import (
    TaskAcceptabilitySensor,
    TaskAcceptabilityObservation,
)
from .agent_guidance import (
    GuidanceAgent,
)
from .sensor_userinput import (
    UserInputSensor,
)
from .actuator_guidance import (
    GuidanceActuator,
    ArrowGuidanceActuator,
    BoxGuidanceActuator,
)
from .actuator_avatar import AvatarActuator

__all__ = (
    # decorators
    "agent_actuator",
    "avatar_actuator",
    "attempt",
    "observe",
    # type alias
    "Agent",
    "Sensor",
    "Actuator",
    # actions
    "ShowElementAction",
    "HideElementAction",
    "DrawArrowAction",
    "DrawBoxAction",
    "DrawBoxOnElementAction",
    "DrawElementAction",
    # sensors
    "UserInputSensor",
    "TaskAcceptabilitySensor",
    # actuators
    "GuidanceActuator",
    "ArrowGuidanceActuator",
    "BoxGuidanceActuator",
    "AvatarActuator",
    # observations
    "TaskAcceptabilityObservation",
    # agents
    "GuidanceAgent",
)
