"""Module that defines a parser for parsing event log files, see also `icua.utils.EventLogger`."""

from datetime import datetime
from pathlib import Path
import pkgutil
import importlib

from star_ray import Event


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
                (ts, e) = self._parse_line(line)
                yield (ts - start_time, e)

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
        return timestamp, cls.model_validate_json(data_str)


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
