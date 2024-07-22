"""Module defines task related events: `DisableTask`, `EnableTask`, see class documentation for details."""

from typing import Any
from star_ray import Event
from pydantic import Field

__all__ = ("EnableTask", "DisableTask")


class DisableTask(Event):
    """Event that disables a given task.

    Attributes:
        task_name (str): name of the task to disable.
    """

    task_name: str


class EnableTask(Event):
    """Event that enables a given task.

    Attributes:
        task_name (str): name of the task to enable.
        context (dict[str,Any]): context to use when enabling the task
        insert_at (int): at what position in the SVG tree to insert the task element.
    """

    task_name: str
    context: dict[str, Any] | None = Field(default=None)
    insert_at: int = Field(default=0)
