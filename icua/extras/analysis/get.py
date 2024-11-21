"""Get various kinds of data from parsed event logs."""

from collections.abc import Callable
import pandas as pd
import inspect
from icua.event.event_avatar import RenderEvent
from icua.extras.analysis.event_log_parser import EventLogParser
from star_ray import Event
from icua.event import (
    ShowGuidance,
    HideGuidance,
    TaskAcceptable,
    TaskUnacceptable,
)
import numpy as np


def get_svg_as_image(
    svg_size: tuple[int, int], events: list[float, Event]
) -> np.ndarray:
    """Get the initial svg that was displayed at the begining of the simulation.

    This can be useful for debugging or visualising mouse/eye positions relative to tasks. The render is static - it doesn't change with updates to the tasks.

    Args:
        svg_size (tuple[int, int]): size of the svg (UI size from configuration).
        events (list[float, Event]): event log

    Returns:
        np.ndarray: rendered svg in HWC uint8 format of size `svg_size`
    """
    from star_ray_xml import Insert
    from star_ray_pygame import SVGAmbient
    from star_ray_pygame.cairosurface import CairoSVGSurface
    from .event_log_parser import EventLogParser

    parser = EventLogParser([])
    insert_events = parser.filter_events(events, Insert)
    # window_resize_events = parser.filter_events(events, WindowResizeEvent)
    # if len(window_resize_events) > 1:
    #     LOGGER.warning(
    #         "Window was resized during simulation, static event visualisation may fail."
    #     )
    state = SVGAmbient([], svg_size=svg_size).get_state()
    for _, event in insert_events:
        state.insert(event)
    svg_root = state.get_root()._base
    # by default, the window size is used as the surface size, see star_ray_pygame.view.View
    surface = CairoSVGSurface(svg_size)
    surface.update(svg_root)
    # matplotlib wants the image in WHC format...
    return surface.render_to_array(svg_size).transpose(1, 0, 2)


def merge_intervals(intervals: np.ndarray, *extra: np.ndarray) -> np.ndarray:
    """Merge overlapping intervals. Intervals are specified by (start,end) as an array of shape (n,2).

    Args:
        intervals (np.ndarray): intervals to merge.
        extra (tuple[np.ndarray], optional): additional array(s) of intervals to merge. The result will be a single array containing merged intervals from `intervals` and `extra`.

    Returns:
        np.ndarray: merged intervals
    """

    def _normalise_types(inter):
        if len(inter) == 0:
            array = np.array([]).reshape(0, 2)
        else:
            array = np.array(intervals)
        assert len(array.shape) == 2
        assert array.shape[1] == 2
        return array

    intervals = np.concatenate([_normalise_types(i) for i in (intervals, *extra)])
    sorted_intervals = intervals[intervals[:, 0].argsort()]
    starts = sorted_intervals[:, 0]
    ends = sorted_intervals[:, 1]
    merged_intervals = []
    current_start = starts[0]
    current_end = ends[0]

    for i in range(1, len(starts)):
        # If the next interval overlaps or touches, merge it
        if starts[i] <= current_end:
            current_end = max(current_end, ends[i])  # Update the current interval's end
        else:
            # If there is no overlap, append the current interval and start a new one
            merged_intervals.append([current_start, current_end])
            current_start = starts[i]
            current_end = ends[i]

    # Append the last interval
    merged_intervals.append([current_start, current_end])
    return np.array(merged_intervals)


def dedup(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Remove consective duplicate rows from `df` by the value in `col`.

    Args:
        df (pd.DataFrame): dataframe to remove duplicate rows from
        col (str): column to use to locate duplicates

    Returns:
        pd.DataFrame: the dedupped dataframe
    """
    return df[df[col] != df[col].shift()]


def isin_intervals(timestamps: np.ndarray, intervals: np.ndarray) -> np.ndarray:
    """Computes a boolean array which indicates whether each timestamp is within an interval in `intervals`, start inclusive, end exclusive.

    Args:
        timestamps (np.ndarray): a 1D array of timestamps.
        intervals (np.ndarray): a 2D array of intervals, where each row is an interval (start, end).

    Returns:
        np.ndarray: a 1D boolean array which is True for each timestamp that is within an interval.
    """
    assert len(intervals.shape) == 2
    assert intervals.shape[1] == 2
    # TODO this is quite slow for many intervals... can do it faster if we sort the arrays
    result = np.zeros(timestamps.shape, dtype=bool)
    for start, end in intervals:
        # Update the result array for timestamps within the current interval
        result |= (timestamps >= start) & (timestamps < end)
    return result


def _generate_intervals(
    events: list[tuple[float, Event]],
    start: type | Callable[[Event], bool],
    end: type | Callable[[Event], bool],
    use_first: bool = False,  # if True the first matching event will be used as the start time
    use_last: bool = False,  # if True the last matching event will be used as the end time
    start_time: float | None = None,
    end_time: float | None = None,
):
    # this should only be used for events are timed by event.timestamp
    # and NOT for events that are timed using the logging timestamp.
    if start_time is None:
        start_time = events[0][1].timestamp

    if end_time is None:
        end_time = events[-1][1].timestamp

    if inspect.isclass(start):

        def start_check(x, _start=start):
            return isinstance(x, _start)

        start_check.__name__ = start.__name__
        start = start_check
    if inspect.isclass(end):

        def end_check(x, _end=end):
            return isinstance(x, _end)

        end_check.__name__ = end.__name__
        end = end_check

    def _gen():
        for t, event in events:
            if start(event):
                yield event.timestamp, event.task, start.__name__
            elif end(event):
                yield event.timestamp, event.task, end.__name__

    for task, df in pd.DataFrame(_gen(), columns=["timestamp", "task", "type"]).groupby(
        "task"
    ):
        # remove consective duplicates, these are meaningless (there shouldnt be any...?)
        df = dedup(df.reset_index(drop=True), col="type").reset_index(drop=True)
        if use_first:
            start_time = df["timestamp"].iloc[0]
        if use_last:
            end_time = df["timestamp"].iloc[-1]
        # insert events if needed
        if df["type"].iloc[0] != start.__name__:
            df = pd.concat(
                [pd.DataFrame([{"timestamp": start_time, "type": start.__name__}]), df]
            ).reset_index(drop=True)

        if df["type"].iloc[-1] != end.__name__:
            df = pd.concat(
                [df, pd.DataFrame([{"timestamp": end_time, "type": end.__name__}])]
            ).reset_index(drop=True)

        assert len(df) % 2 == 0  # must be an even number to create intervals!
        intervals = df["timestamp"].to_numpy().reshape(-1, 2)
        # the first and last intervals may be of size 0, we should remove them if so as
        # they are not useful, and just used to pad the intervals to get an even shape
        if intervals[0, 1] - intervals[0, 0] == 0:
            intervals = intervals[1:]
        if intervals.shape[0] > 0:  # there may not be any intervals left to trim
            if intervals[-1, 1] - intervals[-1, 0] == 0:
                intervals = intervals[:-1]
        yield task, intervals


def get_guidance_intervals(events: list[tuple[float, Event]]):
    """Generator that will get guidance intervals by task. The intervals always start with "ShowGuidance" and end with "HideGuidance".

    Args:
        events (list[tuple[float, Event]]): events from event log

    Yields:
        (str, np.ndarray): task name, intervals
    """
    start, end = ShowGuidance, HideGuidance
    start_time, end_time = get_start_and_end_time(events)
    # guidance always starts off with "ShowGuidance"
    yield from _generate_intervals(
        events, start, end, start_time=start_time, end_time=end_time
    )


def get_frame_timestamps(events: list[tuple[float, Event]]) -> np.ndarray:
    """Get the frame timestamps from the event log.

    This retrives the event timestamp from `RenderEvent` events. The reason we use event timestamps and not logging timestamps, is that the event timestamp is generated at the time the UI frame is rendered to the user. It provides accurate timing for when the user is able to view any changes made to the UI previously. The logging timestamp is generated when the event is logged, which is some short time after the frame was rendered.

    NOTE: user input events (e.g. `MouseButtonEvent`) that happen between two frames (according to their own event timestamp) may not be visible to the user yet. They are guaranteed to be visible on the NEXT frame.

    Args:
        events (list[tuple[float, Event]]): events from event log

    Returns:
        np.ndarray: frame timestamps of shape (n,)
    """
    events = EventLogParser.filter_events(events, RenderEvent)
    return np.array([e.timestamp for _, e in events])


def get_start_and_end_time(events: list[tuple[float, Event]]):
    """Get the start and end time of the experiment from the event log.

    This is the time of the first and last render event.
    Note that these timestamps may not match the first and last events in the log.

    Args:
        events (list[tuple[float, Event]]): events from event log

    Raises:
        ValueError: if no render events are found in the event log

    Returns:
        tuple[float, float]: start and end time of the experiment
    """
    # get the time of the first and last render events
    render_events = EventLogParser.filter_events(events, RenderEvent)
    if len(render_events) == 0:
        raise ValueError("No render events found in event log.")
    return render_events[0][0], render_events[-1][0]


def get_unacceptable_intervals(events: list[tuple[float, Event]]):
    """Generator that will get unacceptability intervals by task.

    The intervals always start with "TaskUnacceptable" and end with "TaskAcceptable" and contain the event timestamp (not the logging timestamp).

    Args:
        events (list[tuple[float, Event]]): events from event log

    Yields:
        (str, np.ndarray): task name, intervals
    """
    # this is the same as get_acceptable_intervals, but with the order of the start and end events reversed
    # the internal function will handle the first event even if it is TaskAcceptable without producing a short
    # unacceptable interval at the begining of the experiment.
    end, start = TaskAcceptable, TaskUnacceptable
    start_time, end_time = get_start_and_end_time(events)
    # we will ignore the time before the task begins, but use time until the final timestamp
    yield from _generate_intervals(
        events,
        start,
        end,
        use_first=True,
        use_last=False,
        start_time=start_time,
        end_time=end_time,
    )


def get_acceptable_intervals(events: list[tuple[float, Event]]):
    """Generator that will get acceptability intervals by task.

    The intervals always start with "TaskAcceptable" and end with "TaskUnacceptable" and contain the event timestamp (not the logging timestamp).

    Args:
        events (list[tuple[float, Event]]): events from event log

    Yields:
        (str, np.ndarray): task name, intervals
    """
    start, end = TaskAcceptable, TaskUnacceptable
    start_time, end_time = get_start_and_end_time(events)
    # we will ignore the time before the task begins, but use time until the final timestamp
    yield from _generate_intervals(
        events,
        start,
        end,
        use_first=True,
        use_last=False,
        start_time=start_time,
        end_time=end_time,
    )


if __name__ == "__main__":
    # TODO move this to a test file...
    from pydantic import BaseModel

    class A(BaseModel):  # noqa
        task: str

    class B(BaseModel):  # noqa
        task: str

    def _events():
        for i in range(10):
            yield i, A(task="task") if i % 2 == 0 else B(task="task")

    events = list(_events())
    for task, intervals in _generate_intervals(events, A, B):
        print(task, intervals)

    def _events():
        for i in range(10):
            yield i, A(task="task") if (i + 1) % 2 == 0 else B(task="task")

    events = list(_events())
    for task, intervals in _generate_intervals(events, A, B):
        print(task, intervals)
