from importlib.resources import files
import os

# directories
# DEFAULT_TASK_PATH = DEFAULT_STATIC_PATH / "task"
# DEFAULT_CONFIG_PATH = DEFAULT_STATIC_PATH / "config"
# DEFAULT_SCHEDULE_PATH = DEFAULT_STATIC_PATH / "schedule"
# # files
# DEFAULT_SVG_INDEX_FILE = DEFAULT_STATIC_PATH / "index.svg.jinja"
# DEFAULT_SERVER_CONFIG_FILE = DEFAULT_CONFIG_PATH / "default_server_config.json"
# DEFAULT_SCHEDULE_FILE = DEFAULT_SCHEDULE_PATH / "default_schedule.sch"

_TASK_PATH = files(__package__) / "tasks"
TASK_ID_TRACKING = "tracking"
TASK_ID_SYSTEM_MONITORING = "system_monitoring"
TASK_ID_RESOURCE_MANAGEMENT = "resource_management"
CONFIG_PATH = _TASK_PATH / "config.schema.json"
assert os.path.exists((str(CONFIG_PATH)))

TASKS = [TASK_ID_TRACKING, TASK_ID_SYSTEM_MONITORING, TASK_ID_RESOURCE_MANAGEMENT]
TASK_PATHS = {t: str(_TASK_PATH / t) for t in TASKS}
for task, path in TASK_PATHS.items():
    assert os.path.exists(str(path))

DEFAULT_ENABLED_TASKS = [
    TASK_ID_TRACKING,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_RESOURCE_MANAGEMENT,
]

DEFAULT_KEY_BINDING = {
    "arrowright": "right",
    "arrowleft": "left",
    "arrowup": "up",
    "arrowdown": "down",
    "right": "right",
    "left": "left",
    "up": "up",
    "down": "down",
}

ALTERNATE_KEY_BINDING = {
    "d": "right",
    "a": "left",
    "w": "up",
    "s": "down",
}


PYGAME_CONST = dict(
    DEFAULT_KEY_BINDING={
        "right": "right",
        "left": "left",
        "up": "up",
        "down": "down",
    },
    ALTERNATE_KEY_BINDING={
        "d": "right",
        "a": "left",
        "w": "up",
        "s": "down",
    },
)
