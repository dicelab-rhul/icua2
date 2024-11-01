"""Functions for extracting user input events from an event log file."""

import pandas as pd
from icua.extras.eyetracking import EyeMotionEvent
from icua.event import (
    Event,
    MouseMotionEvent,
    MouseButtonEvent,
    KeyEvent,
)
from . import EventLogParser
import warnings


def get_keyboard_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get keyboard events from a list of events.

    Columns:
        - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
        - key: str - the key that was pressed.
        - status: int - 0 for RELEASE (UP), 1 for PRESS (DOWN)

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "key", "status"]
    """
    COLUMNS = ["timestamp", "key", "status"]
    keboard_events = parser.filter_events(events, KeyEvent)
    if len(keboard_events) == 0:
        warnings.warn("No keyboard events found in the event log.")
        return pd.DataFrame(columns=COLUMNS)
    keyboard_df = parser.as_dataframe(
        keboard_events, include=["timestamp", "key", "status"]
    )
    return keyboard_df[COLUMNS]


def get_eyetracking_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get eye motion events from a list of events. Note that these events have been processed by filters that smooths and computes fixation information.

    Columns:
    - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
    - x: float - the x position of the mouse when the event occurred.
    - y: float - the y position of the mouse when the event occurred.
    - fixated: bool - whether the eyes are fixated or saccading based on the IVT filter.
    - target: list[str] - the ids of the UI elements that the mouse is hovering over.

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: (timestamp, x, y, fixated, target)
    """
    COLUMNS = ["timestamp", "x", "y", "fixated", "target"]
    eye_motion_events = parser.filter_events(events, EyeMotionEvent)
    if len(eye_motion_events) == 0:
        warnings.warn("No eye motion events found in the event log.")
        return pd.DataFrame(columns=COLUMNS)
    # convert the events from a list to a dataframe. NOTE: that `timestamp_log` is used as the column name for the logging timestamp
    eye_motion_df = parser.as_dataframe(
        eye_motion_events, include=["timestamp", "position", "fixated", "target"]
    )
    eye_motion_df["x"] = eye_motion_df["position"].apply(lambda p: p[0])
    eye_motion_df["y"] = eye_motion_df["position"].apply(lambda p: p[1])
    eye_motion_df.drop(columns=["position"], inplace=True)
    return eye_motion_df[COLUMNS]


def get_mouse_motion_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get mouse motion events from a list of events.

    Columns:
    - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
    - x: float - the x position of the mouse when the event occurred.
    - y: float - the y position of the mouse when the event occurred.
    - target: list[str] - the ids of the UI elements that the mouse is hovering over.

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: (timestamp, x, y, target)
    """
    COLUMNS = ["timestamp", "x", "y", "target"]
    mouse_motion_events = parser.filter_events(events, MouseMotionEvent)
    if len(mouse_motion_events) == 0:
        warnings.warn("No mouse motion events found in the event log.")
        return pd.DataFrame(columns=COLUMNS)
    # convert the events from a list to a dataframe. NOTE: that `timestamp_log` is used as the column name for the logging timestamp
    mouse_motion_df = parser.as_dataframe(
        mouse_motion_events, include=["timestamp", "position", "target"]
    )
    mouse_motion_df["x"] = mouse_motion_df["position"].apply(lambda p: p[0])
    mouse_motion_df["y"] = mouse_motion_df["position"].apply(lambda p: p[1])
    mouse_motion_df.drop(columns=["position"], inplace=True)
    return mouse_motion_df[COLUMNS]


def get_mouse_button_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Get mouse button events from a list of events.

    Columns:
        - timestamp: float - the timestamp of the event. This is not the logging timestamp, but the approximate timestamp of when user actually provided the input.
        - x: float - the x position of the mouse when the event occurred.
        - y: float - the y position of the mouse when the event occurred.
        - button: int - 1 for LEFT, 2 for MIDDLE, 3 for RIGHT
        - status: int - 0 for RELEASE (UP), 1 for PRESS (DOWN)
        - target: list[str] - the ids of the UI elements that the mouse is interacting with.

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "x", "y", "button", "status", "target"]
    """
    COLUMNS = ["timestamp", "x", "y", "button", "status", "target"]
    # print(MouseButtonEvent.__module__ + "." + MouseButtonEvent.__name__)
    # filter events of interest, you can use any event type here, but we are interested in mouse button events
    mouse_button_events = parser.filter_events(events, MouseButtonEvent)
    if len(mouse_button_events) == 0:
        warnings.warn("No mouse button events found in the event log.")
        # there were no mouse button events!
        return pd.DataFrame(columns=COLUMNS)
    mouse_button_df = parser.as_dataframe(
        mouse_button_events,
        include=["timestamp", "position", "button", "status", "target"],
    )
    mouse_button_df["x"] = mouse_button_df["position"].apply(lambda p: p[0])
    mouse_button_df["y"] = mouse_button_df["position"].apply(lambda p: p[1])
    mouse_button_df.drop(columns=["position"], inplace=True)
    return mouse_button_df[COLUMNS]
