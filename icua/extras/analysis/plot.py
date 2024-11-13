"""Module containing useful tools for plotting event occurances."""

from typing import Literal
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from star_ray import Event


def _get_fig_ax(ax: plt.Axes | None = None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 2))
        ax.set_yticks([])
        fig.tight_layout()
    else:
        fig = ax.get_figure()
    return fig, ax


def plot_intervals(
    intervals: np.ndarray,
    color: str = "blue",
    alpha: float = 1.0,
    # linestyle: str = "-",
    # linewidth: float = 1.0,
    ymin: float = 0.0,
    ymax: float = 1.0,
    label: str | None = None,
    ax: plt.Axes | None = None,
):
    """TODO."""
    if isinstance(intervals, pd.DataFrame):
        intervals = intervals[["t1", "t2"]].to_numpy()
    if intervals.shape[0] == 0:
        return _get_fig_ax(ax)[0]

    assert len(intervals.shape) == 2
    assert intervals.shape[1] == 2
    fig, ax = _get_fig_ax(ax)
    for interval in intervals:
        ax.axvspan(
            interval[0],
            interval[1],
            color=color,
            alpha=alpha,
            ymin=ymin,
            ymax=ymax,
            # linestyle=linestyle,
            # linewidth=linewidth,
            label=label,
        )
        label = None
    (xmin, xmax) = ax.get_xlim()
    ax.set_xlim(min(xmin, intervals.min()), max(xmax, intervals.max()))
    return fig


def plot_timestamps(
    timestamps: np.ndarray,
    color: str = "blue",
    alpha: float = 1.0,
    linestyle: str = "-",
    linewidth: float = 1.0,
    ymin: float = 0.0,
    ymax: float = 1.0,
    label: str | None = None,
    ax: plt.Axes | None = None,
):
    """Plot timestamps as vertical lines on an axis.

    Args:
        timestamps (np.ndarray): Timestamps to plot.
        color (str, optional): Color of the lines. Defaults to "blue".
        alpha (float, optional): Alpha value for the lines. Defaults to 1.0.
        linestyle (str, optional): Line style for the lines. Defaults to "-".
        linewidth (float, optional): Line width for the lines. Defaults to 1.0.
        ymin (float, optional): Minimum y-value for the lines. Defaults to 0.0.
        ymax (float, optional): Maximum y-value for the lines. Defaults to 1.0.
        label (str | None, optional): Label for the lines. Defaults to None.
        ax (plt.Axes | None, optional): matplotlib axes to use. Defaults to None.

    Returns:
        figure: Matplotlib figure containing the plot.
    """
    fig, ax = _get_fig_ax(ax)
    for t in timestamps:
        ax.axvline(
            t,
            ymin=ymin,
            ymax=ymax,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            alpha=alpha,
            label=label,
        )
        label = None
    (xmin, xmax) = ax.get_xlim()
    _min, _max = timestamps.min(), timestamps.max()
    ax.set_xlim(min(xmin, _min - (_min * 0.02)), max(xmax, _max + (_max * 0.02)))
    return fig


def plot_events(
    events: list[tuple[float, Event]],
    cls: type,
    mode: Literal["log", "event"] = "log",
    color: str = "blue",
    alpha: float = 1.0,
    linestyle: str = "-",
    linewidth: float = 1.0,
    ymin: float = 0.0,
    ymax: float = 1.0,
    ax: plt.Axes | None = None,
):
    """TODO."""
    events = filter(lambda x: isinstance(x[1], cls), events)

    if mode == "log":
        ts = np.array([x[0] for x in events])
    elif mode == "event":
        ts = np.array([x[1].timestamp for x in events])
    else:
        raise TypeError(f"Invalid mode: {mode}, must be one of {mode.__args__}")

    fig, ax = _get_fig_ax(ax)
    for t in ts:
        ax.axvline(
            t,
            ymin=ymin,
            ymax=ymax,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            alpha=alpha,
        )
    return fig
