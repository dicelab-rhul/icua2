"""Module containing useful tools for plotting event occurances."""

from typing import Literal
import matplotlib.pyplot as plt
import numpy as np
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
    timestamps: np.ndarray,
    color: str = "blue",
    alpha: float = 1.0,
    # linestyle: str = "-",
    # linewidth: float = 1.0,
    ymin: float = 0.0,
    ymax: float = 1.0,
    ax: plt.Axes | None = None,
):
    """TODO."""
    assert len(timestamps.shape) == 2
    assert timestamps.shape[1] == 2
    fig, ax = _get_fig_ax(ax)
    for interval in timestamps:
        ax.axvspan(
            interval[0],
            interval[1],
            color=color,
            alpha=alpha,
            ymin=ymin,
            ymax=ymax,
            # linestyle=linestyle,
            # linewidth=linewidth,
        )
    (xmin, xmax) = ax.get_xlim()
    ax.set_xlim(min(xmin, timestamps.min()), max(xmax, timestamps.max()))
    return fig


def plot_timestamps(
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
