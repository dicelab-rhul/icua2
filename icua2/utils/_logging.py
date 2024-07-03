import logging
import pathlib
from datetime import datetime
from pydantic import BaseModel
from star_ray.pubsub import Subscriber
from star_ray.utils._logging import LOGGER, Indent


class DateTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        if not datefmt:
            return super().formatTime(record)
        return datetime.fromtimestamp(record.created).strftime(datefmt)


class EventLogger(Subscriber):
    def __init__(self, path: str = None):
        path = path if path is not None else EventLogger.default_log_path()
        if isinstance(path, str):
            path = pathlib.Path(path).expanduser().resolve()
        pathlib.Path(path).parent.mkdir(exist_ok=True)
        self.path = str(path)
        self.logger = logging.getLogger(f"{path.name.split('.')[0]}_event_logger")
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(self.path)
        formatter = DateTimeFormatter(
            fmt="%(asctime)s %(message)s", datefmt="%Y-%m-%d-%H-%M-%S-%f"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, event: BaseModel):
        self.logger.info("%s %s", type(event).__name__, event.model_dump())

    def __notify__(self, message: BaseModel):
        self.log(message)

    @staticmethod
    def default_log_path(path=None, name=None):
        if path is None:
            path = "./logs/"
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y-%m-%d-%H-%M-%S")
        name = name if name is not None else f"event_log_{timestamp}.log"
        if "{datetime}" in name:
            name = name.format(datetime=timestamp)
        default_filename = pathlib.Path(path, name).expanduser().resolve()
        return default_filename
