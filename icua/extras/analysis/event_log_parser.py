"""Module that defines a parser for parsing event log files, see also `icua.utils.EventLogger`."""

from datetime import datetime
from pathlib import Path
from collections import defaultdict
from pydantic import ValidationError
from typing import TypeVar

import pkgutil
import importlib
import json
import pandas as pd

from icua.event import RenderEvent
from star_ray import Event
from ...utils import LOGGER


E = TypeVar("E")


class EventLogParser:
    """Parser for event logs."""

    def __init__(self, event_classes: list[type] = None):
        """Constructor.

        Args:
            event_classes (list[type], optional): list of classes that may appear in the event log. Defaults to None.
        """
        super().__init__()
        self._event_cls_map = (
            {c.__name__: c for c in event_classes} if event_classes else {}
        )

    def discover_event_classes(self, module: str):
        """Automatically discover all classes that subclass `star_ray.Event`. This may be slow, so it may be preferable to provide these classes explicitly in the `EventLogParser` constructor (if they are known in advance).

        Note that if a class cannot be found during parsing an exception will be raised, if this happens, try calling this with the module that contains the missing event class.

        Args:
            module (str): module to import from (e.g. "icua")
        """
        for c in discover_subclasses(Event, module):
            self._event_cls_map[c.__name__] = c
            # self._event_cls_map[self.get_fully_qualified_name(c)] = c

    def get_fully_qualified_name(self, event_class: type[Event]) -> str:
        """Get the fully qualified name of an event class."""
        return event_class.__module__ + "." + event_class.__name__

    def get_event_log_file(self, directory: str | Path) -> str:
        """Locates the event log file within a directory.

        Args:
            directory (str | Path): path of the directory to search.

        Returns:
            str: the absolute path of the event log file
        """
        path = Path(directory).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Directory {path.as_posix()} not found")

        log_files = list(
            filter(
                lambda f: f.name.startswith("event_log") and f.suffix == ".log",
                path.iterdir(),
            )
        )
        if len(log_files) == 0:
            raise FileNotFoundError(f"Log file in {path.as_posix()} not found")
        if len(log_files) > 1:
            raise ValueError(f"Multiple log files found in {path.as_posix()}")
        return log_files[0].as_posix()

    @classmethod
    def filter_events(
        cls, events: list[tuple[float, Event]], type: type[E]
    ) -> list[tuple[float, E]]:
        """Filters the list of events to contain only those of the given `type`.

        Args:
            events (list[tuple[float, Event]]): list of events
            type (type[E]): event to retrieve

        Returns:
            list[tuple[float, E]]: list of events of only the given type
        """
        return list(filter(lambda x: isinstance(x[1], type), events))

    def get_event_types(self, events: list[tuple[float, Event]]) -> set[type[Event]]:
        """Get the event types present in the list of parsed events.

        Args:
            events (list[tuple[float, Event]]): events parsed from a log file.

        Returns:
            set[type[Event]]: event types
        """
        return set(map(lambda x: type(x[1]), events))

    def as_dataframe(
        self,
        events: list[tuple[float, Event]],
        exclude: tuple[str] | list[str] = None,
        include: tuple[str] | list[str] = None,
        include_frame: bool = False,
    ):
        """Converts a list of events to collection of pandas data frames containing selected fields as columns.

        Args:
            events (list[tuple[float, Event]]): list of events
            exclude (tuple[str] | list[str], optional): fields to exclude. Defaults to None.
            include (tuple[str] | list[str], optional): fields to include. Defaults to None.
            include_frame (bool, optional): whether to include the frame number in the dataframe (this requires events of type `RenderEvent` to be present in `events`). Defaults to False.

        Returns:
            pandas.DataFrame: a dataframe for each event type: event_type -> dataframe

        Raises:
            ValueError: if multiple event types are found in the list, make use of `filter_events` before calling this, or use `as_dataframes`.
        """
        event_types = self.get_event_types(events)
        if RenderEvent in event_types:
            event_types.remove(RenderEvent)
        elif include_frame:
            raise ValueError(
                "No `RenderEvent`s were found in the event log but `include_frame = True`, did you forget to include `RenderEvent` in your event filter?"
            )

        if len(event_types) > 1:
            raise ValueError(
                f"Found more than one event type when converting events to dataframe, use `as_dataframes` if you want to convert an unfiltered list of events. Event types found: {event_types}"
            )
        result = self.as_dataframes(
            events, include=include, exclude=exclude, include_frame=include_frame
        )
        if len(result) == 0:
            # no events were found... this can happen if all the events were filtered out.
            if include_frame and "frame" not in include:
                columns = [*include, "frame"]
            else:
                columns = [*include]
            return pd.DataFrame(columns=columns)
        return next(iter(result.values()))

    @classmethod
    def sort_by_timestamp(
        cls, events: list[tuple[float, Event]]
    ) -> list[tuple[float, Event]]:
        """Sort a list of events by their timestamp.

        For task-related events - those that update the task state, logging timestamps are used (Update, Insert, ToggleLight, BurnFuelAction, etc.)
        For user-input and flag events, the event timestamp is used (RenderEvent, ShowGuidance, TaskAcceptable, MouseButtonEvent, etc.)

        Internally the `icua.event.XPathQuery` type is used, if an event inherits from this type then it is assumed to modify the state.

        This gives the most consistent picture of what happened during a run, the order of the events can then be used to determine which frame each event occurred in.

        Args:
            events (list[tuple[float, Event]]): events to sort

        Returns:
            list[tuple[float, Event]]: sorted events
        """
        # This is the baseclass of all events that will execute some state change, for these we use the logging timestamp, otherwise we use the event timestamp.
        from icua.event import XPathQuery

        def key(event: tuple[float, Event]) -> float:
            if isinstance(event[1], XPathQuery):
                return event[0]
            return event[1].timestamp

        return sorted(events, key=key)

    def as_dataframes(
        self,
        events: list[tuple[float, Event]],
        exclude: tuple[str] | list[str] = None,
        include: tuple[str] | list[str] = None,
        include_frame: bool = False,
    ) -> dict[type[Event], pd.DataFrame]:
        """Converts a list of events to collection of pandas data frames containing selected fields as columns.

        Args:
            events (list[tuple[float, Event]]): list of events
            exclude (tuple[str] | list[str], optional): fields to exclude. Defaults to None.
            include (tuple[str] | list[str], optional): fields to include. Defaults to None.
            include_frame (bool, optional): whether to include the frame number in the dataframe (this requires events of type `RenderEvent` to be present in `events`). Defaults to False.

        Returns:
            dict[type[Event], pandas.DataFrame]: a dataframe for each event type: event_type -> dataframe
        """
        data = defaultdict(list)
        frame = 0
        log_timestamps = (include is None or "timestamp_log" in include) and (
            exclude is None or "timestamp_log" not in exclude
        )
        for t, event in self.sort_by_timestamp(events):
            if isinstance(event, RenderEvent):
                frame += 1
                continue
            x = event.model_dump(include=include, exclude=exclude)
            if log_timestamps:
                x["timestamp_log"] = t
            if include_frame:
                x["frame"] = frame
            data[type(event)].append(x)
        if include_frame and frame == 0:
            raise ValueError(
                "No `RenderEvent`s were found in the event log but `include_frame = True`, did you forget to include `RenderEvent` in your event filter?"
            )
        return {k: pd.DataFrame(v) for k, v in data.items()}

    def parse(self, file_path: str | Path, relative_start: bool = True):
        """Parse an event log file. The expected format per line is: {TIMESTAMP} {EVENT}.

        Args:
            file_path (str | Path): path to the event log file
            relative_start (bool): where to normalise timestamps to be relative to the first log entry.

        Yields:
            tuple[float, star_ray.Event]: (timestamp, event)
        """
        with open(file_path) as file:
            file_iter = iter(file.readlines())
            (start_time, e) = self._parse_line(next(file_iter))
            if not relative_start:
                yield (start_time, e)
                start_time = 0
            else:
                yield (0, e)
            for line in file_iter:
                result = self._parse_line(line)
                if result:
                    (ts, e) = result
                    ts -= start_time
                    e.timestamp -= start_time
                    yield (ts, e)

    def _parse_timestamp_to_ms(self, timestamp_str: str) -> float:  # noqa
        """Parse a str timestamp to get milliseconds."""
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d-%H-%M-%S-%f")
        return timestamp.timestamp()

    def _parse_line(self, line: str):
        """Parse a line of the event log file, expected format: {TIMESTAMP} {EVENT}."""
        parts = line.split(" ", 2)
        if len(parts) != 3:
            raise ValueError(f"Malformed line: {line}")
        timestamp_str, class_name, data_str = parts
        timestamp = self._parse_timestamp_to_ms(timestamp_str)
        cls = self._event_cls_map.get(class_name, None)
        if cls is None:
            raise ValueError(f"Missing class: {class_name}")
        try:
            model = cls.model_validate_json(data_str)
            return (timestamp, model)
        except ValidationError:
            LOGGER.warning(
                f"Failed to validate: {class_name}(id={json.loads(data_str)['id']}, ...)"
            )
            return None


def import_submodules(package_name: str):
    """Dynamically import all submodules of a package."""
    package = importlib.import_module(package_name)
    package_path = package.__path__

    for loader, module_name, is_pkg in pkgutil.walk_packages(
        package_path, package_name + "."
    ):
        importlib.import_module(module_name)


def find_all_subclasses(cls: type) -> list[type]:
    """Recursively find all subclasses of a given class."""
    subclasses = set(cls.__subclasses__())
    all_subclasses = set(subclasses)

    while subclasses:
        subclass = subclasses.pop()
        nested_subclasses = set(subclass.__subclasses__())
        subclasses.update(nested_subclasses)
        all_subclasses.update(nested_subclasses)

    return list(all_subclasses)


def discover_subclasses(base_class: type, package_name: str) -> list[type]:
    """Ensure all subclasses of a given base class are discovered within a package."""
    import_submodules(package_name)
    return list(sorted(find_all_subclasses(base_class), key=lambda c: c.__module__))
