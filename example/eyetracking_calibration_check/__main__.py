# import os

# os.environ["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"
# from pathlib import Path
# from icua2 import MultiTaskEnvironment
# from icua2.utils import LOGGER

# # TODO this will be moved to icua2...
# from matbii.guidance import GuidanceAgentBase


# class EyetrackingCalibrationAgent(GuidanceAgentBase):
#     pass


# avatar = Avatar(
#     sensors=[],  # relevant sensors are added by default
#     actuators=[],
#     # eyetracker=Avatar.get_default_eyetracker(),
# )

# env = MultiTaskEnvironment(agents=[avatar], wait=0.05)

# env.register_task(
#     name="eyetracking_calibration",
#     path=str(Path(__file__).parent / "task"),
# )
# env.enable_task("eyetracking_calibration")
# env.run()

# # env.register_task(
# #     name=TASK_ID_SYSTEM_MONITORING,
# #     path=["./", TASK_PATHS[TASK_ID_SYSTEM_MONITORING]],
# #     agent_actuators=[SystemMonitoringActuator],
# # )
# # env.enable_task(TASK_ID_SYSTEM_MONITORING)

# # env.register_task(
# #     name=TASK_ID_RESOURCE_MANAGEMENT,
# #     path=["./", TASK_PATHS[TASK_ID_RESOURCE_MANAGEMENT]],
# #     agent_actuators=[ResourceManagementActuator],
# # )
# # env.enable_task(TASK_ID_RESOURCE_MANAGEMENT)
# # env.run()
