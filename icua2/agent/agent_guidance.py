from typing import List, Tuple, Dict, Type, Iterator, Any
from collections import defaultdict, deque
from itertools import islice
from star_ray.agent import AgentRouted, Component, Sensor, Actuator, observe, _TypeRouter
from star_ray.event import (
    Event,
    ErrorObservation,
    ErrorActiveObservation
)


from .acceptability import TaskAcceptabilitySensor, TaskAcceptibilityObservation

from .sensor_userinput import UserInputSensor


class GuidanceAgent(AgentRouted):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        user_input_events: Tuple[Type[Event]],
        user_input_events_history_size: int | List[int] = 50,
    ):
        # this is the guidance agents main sensor, it will sense:
        # user input events (typically) MouseButtonEvent, MouseMotionEvent, KeyEvent
        user_input_sensor = UserInputSensor(
            subscribe_to=[*user_input_events])
        super().__init__([user_input_sensor, *sensors], actuators)
        # agent's beliefs store
        self.beliefs = defaultdict(lambda: None)
        # track the acceptability of each task
        self._is_task_acceptable: Dict[str, bool] = defaultdict(lambda: False)
        self._is_task_active: Dict[str, bool] = defaultdict(lambda: False)

        # set up buffers for storing user input events
        if isinstance(user_input_events_history_size, int):
            user_input_events_history_size = [user_input_events_history_size] * len(
                user_input_events
            )
        self._user_input_events = {
            t: deque(maxlen=hsize)
            for t, hsize in zip(user_input_events, user_input_events_history_size)
        }
        self.add_observe_method(self.on_user_input,
                                self.user_input_types)

    def on_acceptable(self, task: str):
        pass

    def on_unacceptable(self, task: str):
        pass

    def on_active(self, task: str):
        pass

    def on_inactive(self, task: str):
        pass

    @property
    def user_input_types(self):
        return tuple(self._user_input_events.keys())

    def get_latest_user_input(self, event_type: Type, n: int = 1) -> Iterator[Event]:
        try:
            return islice(self._user_input_events[event_type], 0, n)
        except IndexError:
            return None

    @observe
    def on_error(self, observation: ErrorActiveObservation | ErrorObservation, component: Component):
        raise observation.exception()

    @observe
    def on_task_acceptibility(self, observation: TaskAcceptibilityObservation):
        task = observation.values['task']
        was_active = self._is_task_active[task]
        was_acceptable = self._is_task_acceptable[task]
        is_active = observation.values['is_active']
        is_acceptable = observation.values['is_acceptable']
        self._is_task_active[task] = is_active
        self._is_task_acceptable[task] = is_acceptable
        if was_active and not is_active:
            self.on_inactive(task)
        elif not was_active and is_active:
            self.on_active(task)
        if was_acceptable and not is_acceptable:
            self.on_unacceptable(task)
        elif not was_acceptable and is_acceptable:
            self.on_acceptable(task)

    # this is manually added to the event router (see __init__), so no @observe here
    def on_user_input(self, observation: Any):
        assert isinstance(observation, self.user_input_types)
        self._user_input_events[type(
            observation)].appendleft(observation)
