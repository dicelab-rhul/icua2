from importlib.resources import files

# TODO remove some of these.. we dont need them!
# directories
DEFAULT_STATIC_PATH = files(__package__).parent.parent / "static"
DEFAULT_TASK_PATH = DEFAULT_STATIC_PATH / "task"
DEFAULT_CONFIG_PATH = DEFAULT_STATIC_PATH / "config"
DEFAULT_SCHEDULE_PATH = DEFAULT_STATIC_PATH / "schedule"
# files
DEFAULT_SVG_INDEX_FILE = DEFAULT_STATIC_PATH / "index.svg.jinja"
DEFAULT_SERVER_CONFIG_FILE = DEFAULT_CONFIG_PATH / "default_server_config.json"
DEFAULT_SCHEDULE_FILE = DEFAULT_SCHEDULE_PATH / "default_schedule.sch"

DEFAULT_SVG_NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}
DEFAULT_SVG = """<svg:svg id="root" x="0" y="0" xmlns:svg="http://www.w3.org/2000/svg"></svg:svg>"""

# TODO this should be set in config file somewhere
DEFAULT_KEY_BINDING = {
    "ArrowRight": "right",
    "ArrowLeft": "left",
    "ArrowUp": "up",
    "ArrowDown": "down",
}

__all__ = (
    "DEFAULT_STATIC_PATH",
    "DEFAULT_TASK_PATH",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_SCHEDULE_PATH",
    "DEFAULT_SVG_INDEX_FILE",
    "DEFAULT_SERVER_CONFIG_FILE",
    "DEFAULT_SCHEDULE_FILE",
    "DEFAULT_SVG_NAMESPACES",
    "DEFAULT_KEY_BINDING",
)
