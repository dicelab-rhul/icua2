"""Package containing extra functionality that may be useful in icua experiments.

Extras:
    - eyetracking: eyetracking support
    - analysis: tools for post-experiment analysis
"""

from . import analysis
from . import eyetracking

__all__ = ("eyetracking", "analysis")
