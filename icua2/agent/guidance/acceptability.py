from abc import ABC, abstractmethod
from typing import Any


class TaskAcceptabilityTracker(ABC):
    """This class can be used by an agent to track the acceptability of a task. Any subclass should implement the `is_acceptable` method, which should define the conditions under which the task is in an acceptable state (according to the agents beliefs)"""

    @abstractmethod
    def is_acceptable(self, beliefs: Any) -> Any:
        """Checks whether this task is in an acceptable state given the agents beliefs about it.

        Args:
            beliefs (Dict[str, Any]): beliefs about the task.
        """
