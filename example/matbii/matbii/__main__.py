from matbii.guidance import (
    DefaultGuidanceAgent,
    DefaultGuidanceActuator,
    SystemMonitoringTaskAcceptabilitySensor,
    TrackingTaskAcceptabilitySensor,
    ResourceManagementTaskAcceptabilitySensor)
from matbii.tasks import (
    TrackingActuator,
    SystemMonitoringActuator,
    ResourceManagementActuator,
    AvatarTrackingActuator,
    AvatarSystemMonitoringActuator,
    AvatarResourceManagementActuator,
)
from matbii import (
    TASK_PATHS,
    TASK_ID_TRACKING,
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
    CONFIG_PATH,
)
from matbii.agent import Avatar
from icua2 import MultiTaskEnvironment

from icua2.utils import LOGGER
from star_ray.ui import WindowConfiguration
from star_ray.utils import ValidatedEnvironment
from pathlib import Path
import argparse
import os
from pprint import pformat
from logging import INFO, DEBUG

LOGGING_LEVELS = {"debug": DEBUG, "info": INFO}

# avoid a pygame issue on linux...
os.environ["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--config",
    required=False,
    help="Path to the matbii configuration file.",
    default=None,
)
args = parser.parse_args()
config = ValidatedEnvironment.load_and_validate_context(
    str(CONFIG_PATH), args.config)
LOGGER.setLevel(LOGGING_LEVELS[config["logging_level"]])


if args.config:
    LOGGER.debug("Using config file: %s", args.config)
else:
    LOGGER.debug("No config file was specified, using default configuration.")
LOGGER.debug("Configuration:\n%s", pformat(config, indent=0)[1:-1])


window_config = WindowConfiguration(
    x=config["window_x"],
    y=config["window_y"],
    width=config["window_width"],
    height=config["window_height"],
    title=config["window_title"],
    resizable=config["window_resizable"],
    fullscreen=config["window_fullscreen"],
    background_color=config["window_background_color"],
)

eyetracking_config = dict(
    enabled=config["eyetracking_enabled"],
    calibration_check=config["eyetracking_calibration_check"],
    moving_average_n=config["eyetracking_moving_average_n"],
    velocity_threshold=config["eyetracking_velocity_threshold"],
    throttle_events=config["eyetracking_throttle"],
)

experiment_config = config["experiment_info"]
experiment_id = experiment_config["id"]
experiment_duration = experiment_config["duration"]
experiment_path = str(Path(experiment_config["path"]).expanduser().resolve())
if not Path(experiment_path).exists():
    raise ValueError(f"Experiment path: {experiment_path} does not exist.")

participant_config = config["participant_info"]
participant_id = participant_config["id"]

LOGGER.info(
    "------------------------------------------------------------------------------------------"
)
LOGGER.info("%25s %s", "Experiment :", experiment_id)
LOGGER.info("%25s %s", "Experiment path :", experiment_path)
LOGGER.info("%25s %s", "Participant :", participant_id)
LOGGER.info("%25s %s", "Eyetracking enabled :", eyetracking_config["enabled"])
LOGGER.info("%25s %s", "Tasks enabled :", config["enable_tasks"])
LOGGER.info(
    "------------------------------------------------------------------------------------------"
)

avatar = Avatar(
    [],  # relevant sensors are added by default
    [AvatarSystemMonitoringActuator(),
     AvatarTrackingActuator(),
     AvatarResourceManagementActuator()],
    # eyetracker=(
    #     Avatar.get_default_eyetracker(**eyetracking_config)
    #     if eyetracking_config["enabled"]
    #     else None
    # ),
    window_config=window_config,
)

guidance_agent = DefaultGuidanceAgent([
    SystemMonitoringTaskAcceptabilitySensor(),
    ResourceManagementTaskAcceptabilitySensor(),
    TrackingTaskAcceptabilitySensor()],
    # change this actuator for different guidance to be shown (must inherit from GuidanceActuator)
    [DefaultGuidanceActuator(arrow_mode="mouse")]
)

env = MultiTaskEnvironment(
    agents=[avatar, guidance_agent],
    wait=0.05,
    svg_size=config["canvas_size"],
    svg_position=config["canvas_offset"],
    logging_path=config["logging_path"],
)

# NOTE: if you have more tasks to add, add them here! dynamic loading is not enabled by default, if you want to load actuators dynamically, enable it in the ambient.
env.register_task(
    name=TASK_ID_TRACKING,
    path=[experiment_path, TASK_PATHS[TASK_ID_TRACKING]],
    agent_actuators=[TrackingActuator],
)
if TASK_ID_TRACKING in config["enable_tasks"]:
    env.enable_task(TASK_ID_TRACKING)

env.register_task(
    name=TASK_ID_SYSTEM_MONITORING,
    path=[experiment_path, TASK_PATHS[TASK_ID_SYSTEM_MONITORING]],
    agent_actuators=[SystemMonitoringActuator],
)
if TASK_ID_SYSTEM_MONITORING in config["enable_tasks"]:
    env.enable_task(TASK_ID_SYSTEM_MONITORING)

env.register_task(
    name=TASK_ID_RESOURCE_MANAGEMENT,
    path=[experiment_path, TASK_PATHS[TASK_ID_RESOURCE_MANAGEMENT]],
    agent_actuators=[ResourceManagementActuator],
)
if TASK_ID_RESOURCE_MANAGEMENT in config["enable_tasks"]:
    env.enable_task(TASK_ID_RESOURCE_MANAGEMENT)

env.run()
