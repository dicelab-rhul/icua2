"""Module that defines the `GuidanceAgent` class. This type of agent can be used to provide visual feedback or "guidance" to a user based on their actions and the current state of the environment, see class documentation for details."""

from typing import Any
from collections.abc import Iterator
from collections import deque
from itertools import islice
from icua.agent.actuator_guidance import GuidanceActuator
from star_ray.agent import AgentRouted, Component, Sensor, Actuator, observe
from star_ray.event import Event, ErrorObservation, ErrorActiveObservation

from .sensor_acceptability import TaskAcceptabilityObservation, TaskAcceptabilitySensor
from .sensor_userinput import UserInputSensor
from .actuator_acceptability import TaskAcceptabilityActuator
from ..event import TaskAcceptable, TaskUnacceptable


class GuidanceAgent(AgentRouted):
    """Base class for an agent that can provide users with visual guidance. It makes use of the task acceptability sensor API (see `icua.agent.TaskAcceptabilitySensor`) to determine which tasks may require the users attention.

    The following methods will be called at the appropriate moment (e.g. when a task switches from an acceptable state to an unacceptable state), a guidance agent should implement these to decide what the do in each case (e.g. show or hide specific guidance).

    - `on_acceptable(self, task: str)`
    - `on_unacceptable(self, task: str)`
    - `on_active(self, task: str)`
    - `on_inactive(self, task: str)`

    A history of user input events are also recorded and can be conveniently accessed via the `get_latest_user_input(self, event_type: type, n: int = 1) -> Iterator[Event]` method.
    """

    def __init__(
        self,
        sensors: list[Sensor],
        actuators: list[Actuator],
        user_input_events: tuple[type[Event]] = None,
        user_input_events_history_size: int | list[int] = 50,
    ):
        """Constructor.

        Args:
            sensors (list[Sensor]): list of sensors, this will typically be a list of `icua.agent.TaskAcceptabilitySensor`s. A `UserInputSensor` will always be added automatically.
            actuators (list[Actuator]): list of actuators, this will typically contain actuators that are capable of providing visual feedback to a user, see e.g. `icua.agent.GuidanceActuator` and its concrete implementations.
            user_input_events (tuple[type[Event]], optional): additional user input events to subscribe to. Defaults to None.
            user_input_events_history_size (int | list[int], optional): size of the history of user input events to keep, when this size is reached old events will be overwritten. Defaults to 50.
        """
        # agent's beliefs store
        self.beliefs = dict()
        # this is the guidance agents main sensor, it will sense:
        # user input events (typically) MouseButtonEvent, MouseMotionEvent, KeyEvent
        user_input_events = user_input_events if user_input_events else []
        user_input_sensor = UserInputSensor(subscribe_to=[*user_input_events])
        user_input_events = user_input_sensor._subscribe_to

        # used when tasks change their acceptability status (receives TaskAcceptable and TaskUnacceptable actions)
        # TODO perhaps we need one for tasks that are active/inactive)
        # but EnableTask and DisableTask may serve this purpose...
        _task_acceptability_actuator = TaskAcceptabilityActuator()
        super().__init__(
            [user_input_sensor, *sensors],
            [_task_acceptability_actuator, *actuators],
        )
        # set up buffers for storing user input events
        if isinstance(user_input_events_history_size, int):
            user_input_events_history_size = [user_input_events_history_size] * len(
                user_input_events
            )
        # TODO use a default dict for this, what if additional subscriptions are made in the UserInputSensor!
        self._user_input_events = {
            t: deque(maxlen=hsize)
            for t, hsize in zip(user_input_events, user_input_events_history_size)
        }
        # add an observe method to capture all user input events (based on the UserInputSensor types)
        self.add_observe(self.on_user_input, self.user_input_types)

    def add_component(self, component: Component) -> Component:  # noqa
        result = super().add_component(component)
        # initialise beliefs for the new task
        if isinstance(result, TaskAcceptabilitySensor):
            self.beliefs[result.task_name] = dict(is_active=False, is_acceptable=False)
        return result

    @property
    def acceptability_sensors(self) -> list[TaskAcceptabilitySensor]:
        """Getter for task acceptability sensors (sensors that derive the type: `icua.agent.TaskAcceptabilitySensor`).

        Returns:
            list[TaskAcceptabilitySensor]: the sensors.
        """
        return list(self.get_sensors(oftype=TaskAcceptabilitySensor))

    @property
    def guidance_actuators(self) -> list[GuidanceActuator]:
        """Getter for guidance actuators (actuators that derive the type: `icua.agent.GuidanceActuator`).

        Returns:
            list[GuidanceActuator]: the GuidanceActuator.
        """
        candidates = list(self.get_actuators(oftype=GuidanceActuator))
        if len(candidates) == 0:
            raise ValueError(
                f"Missing required actuator of type: `{GuidanceActuator.__qualname__}`"
            )
        return candidates

    def on_acceptable(self, task: str):
        """Called when a task enters an acceptable state.

        Args:
            task (str): the task.
        """
        pass

    def on_unacceptable(self, task: str):
        """Called when a task enters an unacceptable state.

        Args:
            task (str): the task.
        """
        pass

    def on_active(self, task: str):
        """Called when a task is made active, typically this means it has been enabled in the environment state, but otherwise it may be that the task has appeared to the user (e.g. if it was previously hidden or not ready for user interaction).

        Args:
            task (str): the task.
        """
        pass

    def on_inactive(self, task: str):
        """Called when a task is made inactive, typically this means it has been disabled in the environment state, but otherwise it may be that the task is just hidden or not ready for user interaction.

        Args:
            task (str): the task.
        """
        pass

    @property
    def user_input_types(self):
        """The types of user input that this agent is tracking (READ ONLY)."""
        # TODO this should be retrieved directly from the UserInputSensor, we dont want copies of this around...
        return tuple(self._user_input_events.keys())

    def get_latest_user_input(self, event_type: type, n: int = 1) -> Iterator[Event]:
        """Getter for the lastest user input of a given type.

        Args:
            event_type (type): the type of user input to get.
            n (int, optional): the number of events to retrieve. Defaults to 1 (the latest event).

        Returns:
            Iterator[Event]: an iterator that contains the requested events (may be empty if no such events exist).
        """
        try:
            return islice(self._user_input_events[event_type], 0, n)
        except IndexError:
            return iter([])
        except KeyError:
            return iter([])

    @observe
    def on_error(
        self,
        observation: ErrorActiveObservation | ErrorObservation,
        component: Component,
    ):
        """Called if this agent receives an `star_ray.event.ErrorObservation` from a component. By default this will re-raise the exception that the observation contains. This can be overriden to alter the default behaviour. The overriding method must be decorated with the `@observe` decorator to work correctly. This method should not be called manually and will be handled by this agents event routing mechanism.

        Args:
            observation (ErrorActiveObservation | ErrorObservation): the error observation.
            component (Component): the component that the observation originated from.

        Raises:
            observation.exception: the exception contained in the observation (raised by default).
        """
        raise observation.exception()

    @observe
    def on_task_acceptability(self, observation: TaskAcceptabilityObservation):
        """Called if this agent receives a `icua.agent.TaskAcceptabilityObservation` from one of its sensors.

        This will trigger the relevant callback:
        - `on_acceptable(self, task: str)`
        - `on_unacceptable(self, task: str)`
        - `on_active(self, task: str)`
        - `on_inactive(self, task: str)`

        This method should not be called manually and will be handled by this agent's event routing mechanism.

        Args:
            observation (TaskAcceptabilityObservation): the acceptability observation
        """
        task = observation.values["task"]
        was_active = self.beliefs[task]["is_active"]
        was_acceptable = self.beliefs[task]["is_acceptable"]
        is_active = observation.values["is_active"]
        is_acceptable = observation.values["is_acceptable"]
        self.beliefs[task]["is_active"] = is_active
        self.beliefs[task]["is_acceptable"] = is_acceptable
        if was_active and not is_active:
            self.on_inactive(task)
        elif not was_active and is_active:
            self.on_active(task)
        if was_acceptable and not is_acceptable:
            self.attempt(TaskUnacceptable(task=task))
            self.on_unacceptable(task)
        elif not was_acceptable and is_acceptable:
            self.attempt(TaskAcceptable(task=task))
            self.on_acceptable(task)

    # this is manually added to the event router (see __init__), so no @observe here
    def on_user_input(self, observation: Any):
        """Called when this agent receives a user input event, it will add the event to an internal buffer. See `get_latest_user_input`.

        This method should not be called manually and will be handled by this agents event routing mechanism.

        Args:
            observation (Any): the observation.
        """
        # print("USER INPUT:", observation)
        assert isinstance(observation, self.user_input_types)
        self._user_input_events[type(observation)].appendleft(observation)

    @property
    def monitoring_tasks(self) -> set[str]:
        """Get the set of tasks that this guidance agent is monitoring.

        Returns:
            set[str]: set of tasks that this agent is monitoring.
        """
        return set([s.task_name for s in self.acceptability_sensors])

    @property
    def active_tasks(self) -> set[str]:
        """Get the set of active tasks.

        Returns:
            set[str]: set of active tasks.
        """
        return set(t for t in self.monitoring_tasks if self.beliefs[t]["is_active"])

    @property
    def inactive_tasks(self) -> set[str]:
        """Get the set of inactive tasks.

        Returns:
            set[str]: set of inactive tasks.
        """
        return set(t for t in self.monitoring_tasks if not self.beliefs[t]["is_active"])

    @property
    def acceptable_tasks(self) -> set[str]:
        """Get the set of acceptable tasks, these do not include inactive tasks.

        Returns:
            set[str]: set of acceptable tasks.
        """
        return set(t for t in self.active_tasks if self.beliefs[t]["is_acceptable"])

    @property
    def unacceptable_tasks(self) -> set[str]:
        """Get the set of unacceptable tasks, these do not include inactive tasks.

        Returns:
            set[str]: set of unacceptable tasks.
        """
        return set(t for t in self.active_tasks if not self.beliefs[t]["is_acceptable"])
