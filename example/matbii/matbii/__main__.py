from icua2 import MultiTaskEnvironment
from star_ray_pygame.avatar import Avatar
from star_ray.agent import Actuator, attempt
from star_ray.event.user_event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    ExitEvent,
)

from matbii import (
    TASK_PATHS,
    TASK_ID_TRACKING,
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
)
from matbii.tasks import (
    TrackingActuator,
    SystemMonitoringActuator,
    ResourceManagementActuator,
    AvatarTrackingActuator,
    AvatarSystemMonitoringActuator,
    AvatarResourceManagementActuator,
)
from matbii.guidance import GuidanceAgentBase, GuidanceAgentDefault


class DefaultActuator(Actuator):

    @attempt(route_events=(MouseButtonEvent, MouseMotionEvent, KeyEvent))
    def default(self, action):
        return action


class ExitActuator(Actuator):

    @attempt(route_events=[ExitEvent])
    def exit(self, action: ExitEvent):
        assert isinstance(action, ExitEvent)
        return action


# TODO actuators should be provided along with the task..?
avatar = Avatar(
    actuators=[
        ExitActuator(),
        DefaultActuator(),  # This actuator enables recording of all user input!
        AvatarSystemMonitoringActuator(),
        AvatarTrackingActuator(),
        AvatarResourceManagementActuator(),
    ]
)
guidance_agent = GuidanceAgentBase()
guidance_agent = GuidanceAgentDefault()

env = MultiTaskEnvironment(agents=[avatar, guidance_agent], wait=0.05)

# load tasks
# for task, task_path in TASK_PATHS.items():
#     env.register_task(name=task, path=task_path, enable=True)

env.register_task(
    name=TASK_ID_TRACKING,
    path=TASK_PATHS[TASK_ID_TRACKING],
    agent_actuators=[TrackingActuator],
)
env.enable_task(TASK_ID_TRACKING)
env.register_task(
    name=TASK_ID_SYSTEM_MONITORING,
    path=TASK_PATHS[TASK_ID_SYSTEM_MONITORING],
    agent_actuators=[SystemMonitoringActuator],
)
env.enable_task(TASK_ID_SYSTEM_MONITORING)
env.register_task(
    name=TASK_ID_RESOURCE_MANAGEMENT,
    path=TASK_PATHS[TASK_ID_RESOURCE_MANAGEMENT],
    agent_actuators=[ResourceManagementActuator],
)
env.enable_task(TASK_ID_RESOURCE_MANAGEMENT)
env.run()
