"""Package containing tools for post-experiment analysis."""

from .event_log_parser import EventLogParser
from .plot import (
    plot_timestamps,
    plot_intervals,
)
from .get import (
    get_svg_as_image,
    get_guidance_intervals,
    get_acceptable_intervals,
    get_unacceptable_intervals,
    get_start_and_end_time,
    get_frame_timestamps,
    merge_intervals,
    dedup,
    isin_intervals,
)
from .get_user_input import (
    get_mouse_motion_events,
    get_mouse_button_events,
    get_attention_intervals,
    get_keyboard_events,
    get_eyetracking_events,
)


__all__ = (
    "EventLogParser",
    "plot_timestamps",
    "plot_intervals",
    "get_attention_intervals",
    "get_guidance_intervals",
    "get_acceptable_intervals",
    "get_unacceptable_intervals",
    "get_svg_as_image",
    "get_start_and_end_time",
    "get_frame_timestamps",
    "merge_intervals",
    "isin_intervals",
    "dedup",
    "get_mouse_motion_events",
    "get_mouse_button_events",
    "get_keyboard_events",
    "get_eyetracking_events",
)
