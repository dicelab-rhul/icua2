import logging
import pathlib
from datetime import datetime
from pydantic import BaseModel
from star_ray.utils._logging import LOGGER, Indent


class DateTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        if not datefmt:
            return super().formatTime(record, datefmt=datefmt)
        return datetime.fromtimestamp(record.created)


class EventLogger:
    def __init__(self, path: str = None):
        path = path if path is not None else EventLogger.default_log_path()
        pathlib.Path(path).parent.mkdir(exist_ok=True)
        self.path = str(path)
        self.logger = logging.getLogger(f"{__name__}_event_logger")
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(self.path)
        formatter = DateTimeFormatter(
            fmt="%(asctime)s %(message)s", datefmt="%Y-%m-%d-%H-%M-%S.%f"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, event: BaseModel):
        self.logger.info(event.model_dump())

    @staticmethod
    def default_log_path(path="./logs/", name=None):
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y-%m-%d-%H-%M-%S")
        name = name if name is not None else f"event_log_{timestamp}.log"
        default_filename = pathlib.Path(path, name).expanduser().resolve()
        return default_filename
