"""Package contains eyetracking related functionality. It supports common eyetracker SDKs and integrates them with the `star_ray` event API.

See:
    - `EyetrackerBase`: base class for all eyetrackers.
    - `tobii` package: implementation of `EyetrackerBase` using tobii eyetracking SDK (requires `tobii_research` package).
"""

from .eyetrackerbase import EyetrackerBase
from .event import EyeMotionEvent
from .filter import IVTFilter, NWMAFilter, WindowSpaceFilter

# requires extra "tobii"
from . import tobii

__all__ = (
    # events
    "EyeMotionEvent",
    # filters
    "IVTFilter",
    "NWMAFilter",
    "WindowSpaceFilter",
    # eyetracker base
    "EyetrackerBase",
    "tobii",  # tobii base eyetracker
)
