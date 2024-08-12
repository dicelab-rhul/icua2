"""Get various kinds of data from parsed event logs."""

from collections.abc import Callable
import pandas as pd
import inspect
from star_ray import Event
from icua.event import (
    ShowGuidance,
    HideGuidance,
    TaskAcceptable,
    TaskUnacceptable,
)


def dedup(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Remove consective duplicates from df by the value in `col`.

    Args:
        df (pd.DataFrame): dataframe to remove values from.
        col (str): column to use

    Returns:
        pd.DataFrame: the dedupped dataframe
    """
    return df[df[col] != df[col].shift()]


def _generate_task_intervals(
    events: list[tuple[float, Event]],
    start: type | Callable[[Event], bool],
    end: type | Callable[[Event], bool],
):
    start_time, end_time = events[0][0], events[-1][0]

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
                yield t, event.task, start.__name__
            elif end(event):
                yield t, event.task, end.__name__

    for task, df in pd.DataFrame(_gen(), columns=["timestamp", "task", "type"]).groupby(
        "task"
    ):
        # print(task, df)
        # remove consective duplicates, these are meaningless (there shouldnt be any...?)
        df = dedup(df.reset_index(drop=True), col="type").reset_index(drop=True)
        # insert events if needed
        if df["type"].iloc[0] != start.__name__:
            df = pd.concat(
                [pd.DataFrame([{"timestamp": start_time, "type": start.__name__}]), df]
            ).reset_index(drop=True)

        if df["type"].iloc[-1] != end.__name__:
            df = pd.concat(
                [df, pd.DataFrame([{"timestamp": end_time, "type": end.__name__}])]
            ).reset_index(drop=True)

        assert len(df) % 2 == 0  # must be an event number to create intervals!
        intervals = df["timestamp"].to_numpy().reshape(-1, 2)
        yield task, intervals


# def get_mouse_click_intervals(events: list[tuple[float, Event]]):
#     def mouse_down(event: MouseButtonEvent):
#         return event.status == MouseButtonEvent.DOWN

#     def mouse_up(event: MouseButtonEvent):
#         return event.status == MouseButtonEvent.UP

#     yield from _generate_task_intervals(events, mouse_down, mouse_up)


# def get_mouse_down_on(events: list[tuple[float, Event]], element: str) -> np.ndarray:
#     events = filter(
#         lambda x: isinstance(x[1], MouseButtonEvent) and element in x[1].target, events
#     )
#     return np.array([e[0] for e in events])


def get_guidance_intervals(events: list[tuple[float, Event]]):
    """Generator that will get guidance intervals by task. The intervals always start with "ShowGuidance" and end with "HideGuidance".

    Args:
        events (list[tuple[float, Event]]): events from event log

    Yields:
        (str, np.ndarray): task name, intervals
    """
    start, end = ShowGuidance, HideGuidance
    yield from _generate_task_intervals(events, start, end)


def get_acceptable_intervals(events: list[tuple[float, Event]]):
    """Generator that will get acceptability intervals by task. The intervals always start with "TaskAcceptable" and end with "TaskUnacceptable".

    Args:
        events (list[tuple[float, Event]]): events from event log

    Yields:
        (str, np.ndarray): task name, intervals
    """
    start, end = TaskAcceptable, TaskUnacceptable
    yield from _generate_task_intervals(events, start, end)


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
    for task, intervals in _generate_task_intervals(events, A, B):
        print(task, intervals)

    def _events():
        for i in range(10):
            yield i, A(task="task") if (i + 1) % 2 == 0 else B(task="task")

    events = list(_events())
    for task, intervals in _generate_task_intervals(events, A, B):
        print(task, intervals)
