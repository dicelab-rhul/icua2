"""Module contains the LoggerActuator class, which may be used by an agent for logging purposes. It makes use of the `loguru` package for logging functionality."""

from datetime import datetime
from typing import Any
import json

import logging
from logging.handlers import RotatingFileHandler

from star_ray import Actuator, attempt
from star_ray.event import Event, Action

__all__ = ("LogAction", "LogActuator")


class LogAction(Action):
    """Action used to log information."""

    level: str = "INFO"
    message: Any


class LogActuator(Actuator):
    """Actuator that may be used for logging."""

    def __init__(
        self,
        path: str,
        rotate: int = 10485760,
        **kwargs: dict[str, Any],
    ):
        """Constructor.

        Args:
            path (str): path to log to
            rotate (int, optional): size of log file before rotating. Defaults to 1mb.
            kwargs (dict[str,Any], optional): additional keyword arguments.
        """
        super().__init__()
        self._logger = logging.getLogger(str(self.id))
        self._logger.setLevel(logging.DEBUG)
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        handler = RotatingFileHandler(path, mode="w", maxBytes=rotate, backupCount=0)
        handler.setFormatter(LogActuator._Formatter(self.format_record))
        self._logger.addHandler(handler)

    def format_timestamp(self, timestamp: float | datetime) -> str:
        """Format the given timestamp, the timestamp is given in unix time (from `time.time()`) or as a datetime object. This is used by the default record formatter `format_record` if the method is overriden then `format_timestamp` may not be called at all.

        By default the timestamp is in seconds format to 8dp from the given epoch.

        Args:
            timestamp (float): the timestamp to format
        """
        if isinstance(timestamp, float):
            return f"{timestamp:.8f}"
        elif isinstance(timestamp, datetime):
            return f"{timestamp.timestamp():.8f}"
        else:
            raise TypeError(f"Unknown timestamp type {type(timestamp)}")

    def format_record(self, record: dict[str, Any]) -> str:
        """Formatter for loguru records received by this log actuator.

        Args:
            record (dict[str, Any]): record to log (see loguru formatting documentation).

        Returns:
            str: formatted record ready for logging
        """
        message = record["message"]
        if isinstance(message, Event):
            cls = message.__class__
            message = dict(
                type=f"{cls.__module__}.{cls.__qualname__ }",
                data=message.model_dump(),
            )
            message = json.dumps(message)
        return f"{self.format_timestamp(record['timestamp'])} {message}"

    @attempt([])  # dont automatically forward events for logging
    def log(self, message: Any) -> LogAction:
        """Log the given message. The message will not be immediately logged, instead it will be logged during action execution.

        Args:
            message (Any): message to log

        Returns:
            LoguruAction: log action
        """
        action = LogAction(source=self.id, message=message)
        Actuator.set_action_source(self, action)
        return action

    def __query__(self, _) -> None:
        """By-passes the usual environment interaction and directly log what has been buffered by the attached agent."""
        actions = self.__attempt__()
        if not isinstance(actions, list | tuple):
            raise TypeError(
                f"`__attempt__` must return a `tuple` of actions, received: {actions}"
            )
        self._actions.extend(actions)
        self._actions = list(filter(None, self._actions))
        # set the source of these actions to this actuator
        Actuator.set_action_source(self, self._actions)
        for action in self._actions:
            assert isinstance(action, LogAction)
            self._logger.log(logging.DEBUG, action)
        self._actions.clear()

    class _Formatter(logging.Formatter):
        def __init__(self, format_method, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.format_method = format_method

        def format(self, record: logging.LogRecord):
            action = record.msg
            # TODO we will want to include more information than this at some point, it is ok for now
            # print("format!", action)
            return self.format_method(
                dict(
                    level=action.level,
                    message=action.message,
                    timestamp=action.timestamp,
                )
            )
