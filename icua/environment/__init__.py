"""Package contains environment related functionality, including support for "multi-task" environments.

See:
    - `MultiTaskEnvironment` and `MultiTaskAmbient` classes for multi-task support.
"""

from .multitask_ambient import MultiTaskAmbient
from .multitask_environment import MultiTaskEnvironment

__all__ = (
    "MultiTaskEnvironment",
    "MultiTaskAmbient",
)
