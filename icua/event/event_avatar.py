"""Module containing events that may be useful for an avatar or for event logging."""

from star_ray.event import Event


class RenderEvent(Event):
    """Event used to indicate that the UI is being rendered by an avatar, has no effect and is used for logging purposes."""
