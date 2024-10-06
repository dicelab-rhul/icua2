import os
import sys
import time
import logging

from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from loguru import logger as _logger
from loguru._logger import Logger  # this is just a type hint

__all__ = ("Logger", "LOGGER")

from star_ray.pubsub import Subscriber


_CWD_DIRECTORY = Path(os.getcwd())


def format_record(record):
    file_path = Path(record["file"].path)
    try:
        file_path = file_path.relative_to(_CWD_DIRECTORY)
    except ValueError:
        pass

    # Format the log message
    return "{level} | {file}:{line} | {message}\n".format(
        # time=record["time"].strftime("%H:%M:%S"),
        level=record["level"].name,
        file=str(file_path),
        line=record["line"],
        message=record["message"],
    )


# Configure the logger
LOGGER = _logger.bind(package="icua")


def set_level(level: str):
    LOGGER.remove()
    LOGGER.add(
        sink=sys.stdout,
        format=format_record,
        level=level,
    )


LOGGER.set_level = set_level

# default level
LOGGER.set_level("DEBUG")

__all__ = ("LOGGER",)


class DateTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        if not datefmt:
            return super().formatTime(record)
        return datetime.fromtimestamp(record.created).strftime(datefmt)


class EventLogger(Subscriber):
    def __init__(self, path: str = None):
        path = path if path is not None else EventLogger.default_log_path()
        if isinstance(path, str):
            path = Path(path).expanduser().resolve()
        Path(path).parent.mkdir(exist_ok=True)
        self.path = str(path)
        self.logger = logging.getLogger(f"{path.name.split('.')[0]}_event_logger")
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(self.path)
        # TODO REMOVE DEPRECATED - time stamp is now set in log to be more in line with event execution times
        # formatter = DateTimeFormatter(
        #     fmt="%(asctime)s %(message)s", datefmt="%Y-%m-%d-%H-%M-%S-%f"
        # )
        # file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, event: BaseModel):
        t = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d-%H-%M-%S-%f")
        self.logger.info("%s %s %s", t, type(event).__name__, event.model_dump_json())

    def __notify__(self, event: BaseModel):
        self.log(event)

    @staticmethod
    def default_log_path(path=None, name=None):
        if path is None:
            path = "./logs/"
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y-%m-%d-%H-%M-%S")
        name = name if name is not None else f"event_log_{timestamp}.log"
        if "{datetime}" in name:
            name = name.format(datetime=timestamp)
        default_filename = Path(path, name).expanduser().resolve()
        return default_filename
