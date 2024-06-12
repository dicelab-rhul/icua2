from icua2 import MultiTaskEnvironment
from star_ray_pygame import WindowConfiguration
from matbii.agent import Avatar

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

# TODO actuators should be provided along with the task..?
avatar = Avatar(
    sensors=[],  # relevant sensors are added by default
    actuators=[
        AvatarSystemMonitoringActuator(),
        AvatarTrackingActuator(),
        AvatarResourceManagementActuator(),
    ],
    eyetracker=None,
    window_config=WindowConfiguration(width=640, height=640, title="matbii"),
)
# guidance_agent = GuidanceAgentBase()
# guidance_agent = GuidanceAgentDefault()
# env = MultiTaskEnvironment(agents=[avatar, guidance_agent], wait=0.05)
env = MultiTaskEnvironment(agents=[avatar], wait=0.05)

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
