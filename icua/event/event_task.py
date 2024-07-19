from typing import Dict, Any
from star_ray import Event
from pydantic import Field

__all__ = ("EnableTask", "DisableTask")


class DisableTask(Event):
    task_name: str


class EnableTask(Event):
    task_name: str
    context: Dict[str, Any] | None = Field(default=None)
    insert_at: int = Field(default=0)
