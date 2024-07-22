"""Module that contains the abstract class `EyetrackerBase` which provides a straight forward API for eyetracking. Typically an `EyetrackerBase` subclass is implemented via an eyetracker hardware provider SDK (see e.g. `TobiiEyetracker`)."""

from abc import ABC, abstractmethod
from star_ray import Event


class EyetrackerBase(ABC):
    """Abstract base class for eyetrackers."""

    @abstractmethod
    def start(self) -> None:
        """Start the eyetracker."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the eyetracker."""

    @abstractmethod
    async def get(self) -> list[Event]:
        """Get the most recent eyetracking events. Will await the next event if there are none pending.

        Returns:
            list[Event]: recent eyetracking events (most recent first).
        """

    @abstractmethod
    def get_nowait(self) -> list[Event]:
        """Get the most recent eyetracking events, will return an empty list if there are no pending events.

        Returns:
            list[Event]: recent eyetracking events (most recent first).
        """
