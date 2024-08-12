"""Module defines an actuator that will take actions indicating that a task has changed its acceptability status (see `icua.event.TaskAcceptable` and `icua.event.TaskUnacceptable`)."""

from star_ray import Actuator, attempt
from icua.event import TaskAcceptable, TaskUnacceptable


class TaskAcceptabilityActuator(Actuator):
    """Abstract base class for guidance actuators."""

    @attempt
    def on_acceptable(self, action: TaskAcceptable):
        """An attempt method that will show guidance to a user."""
        return action

    @attempt
    def on_unacceptable(self, action: TaskUnacceptable):
        """An attempt method that will hide guidance from a user."""
        return action
