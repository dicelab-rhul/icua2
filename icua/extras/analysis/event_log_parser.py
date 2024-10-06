"""Module that defines a parser for parsing event log files, see also `icua.utils.EventLogger`."""

from datetime import datetime
from pathlib import Path
from collections import defaultdict
from pydantic import ValidationError

import pkgutil
import importlib
import json
import pandas as pd

from star_ray import Event
from ...utils import LOGGER


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

    def get_event_log_file(self, directory: str | Path) -> str | list[str]:
        """Locates the log file within a directory.

        Args:
            directory (str | Path): path of the directory to search.

        Returns:
            str | list[str]: the absolute path(s) of the log files
        """
        path = Path(directory).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Directory {path.as_posix()} not found")

        log_files = list(
            filter(
                lambda f: f.name.startswith("event_log") or f.suffix == ".log",
                path.iterdir(),
            )
        )
        if len(log_files) == 0:
            raise FileNotFoundError(f"Log file in {path.as_posix()} not found")
        if len(log_files) > 1:
            raise ValueError(f"Multiple log files found in {path.as_posix()}")
        return log_files[0].as_posix()

    def filter_events(
        self, events: list[tuple[float, Event]], type: type[Event]
    ) -> list[tuple[float, Event]]:
        """Filters the list of events to contain only those of the given `type`.

        Args:
            events (list[tuple[float, Event]]): list of events
            type (type[Event]): event to retrieve

        Returns:
            list[tuple[float, Event]]: list of events of only the given type
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
    ):
        """Converts a list of events to collection of pandas data frames containing selected fields as columns.

        Args:
            events (list[tuple[float, Event]]): list of events
            exclude (tuple[str] | list[str], optional): fields to exclude. Defaults to None.
            include (tuple[str] | list[str], optional): fields to include. Defaults to None.

        Returns:
            pandas.DataFrame: a dataframe for each event type: event_type -> dataframe

        Raises:
            ValueError: if multiple event types are found in the list, make use of `filter_events` before calling this, or use `as_dataframes`.
        """
        event_types = self.get_event_types(events)
        if len(event_types) > 1:
            raise ValueError(
                f"Found more than one event type when converting events to dataframe, use `as_dataframes` if you want to convert an unfiltered list of events. Event types found: {event_types}"
            )
        result = self.as_dataframes(events, include=include, exclude=exclude)
        assert len(result.keys()) == 1
        return next(iter(result.values()))

    def as_dataframes(
        self,
        events: list[tuple[float, Event]],
        exclude: tuple[str] | list[str] = None,
        include: tuple[str] | list[str] = None,
    ) -> dict[type[Event], pd.DataFrame]:
        """Converts a list of events to collection of pandas data frames containing selected fields as columns.

        Args:
            events (list[tuple[float, Event]]): list of events
            exclude (tuple[str] | list[str], optional): fields to exclude. Defaults to None.
            include (tuple[str] | list[str], optional): fields to include. Defaults to None.

        Returns:
            dict[type[Event], pandas.DataFrame]: a dataframe for each event type: event_type -> dataframe
        """
        data = defaultdict(list)
        for t, event in events:
            x = event.model_dump(include=include, exclude=exclude)
            if (include is None or "timestamp_log" in include) and (
                exclude is None or "timestamp_log" not in exclude
            ):
                x["timestamp_log"] = t
            data[type(event)].append(x)
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
            yield (start_time, e)
            if not relative_start:
                start_time = 0
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
