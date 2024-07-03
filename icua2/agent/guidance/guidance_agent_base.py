from typing import List, Tuple, Dict, Type, Iterator
from collections import defaultdict, deque
from itertools import islice
from star_ray.agent import Agent, Component, Sensor, Actuator, attempt
from star_ray.event import (
    Event,
    Observation,
    ErrorObservation,
)

from star_ray.pubsub import Subscribe
from star_ray_xml import select

from .acceptability import TaskAcceptabilityTracker


class ActiveGuidanceSensor(Sensor):
    # TODO subscriptions in XMLState (e.g. subscribe to changes for a particular element with an id)

    def __init__(self, subscribe_to: List[Type[Event]] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribe_to = subscribe_to if subscribe_to else []

    @attempt
    def sense(self, actions: List[Event]):
        # continuously get data relevant for task acceptability
        return actions

    @attempt
    def sense_element(self, element_id: str, *attrs):
        attrs = set(attrs)
        attrs.add("id")
        return select(xpath=f"//*[@id='{element_id}']", attrs=attrs)

    def __subscribe__(self):
        return [Subscribe(topic=event_type) for event_type in self._subscribe_to]


class GuidanceAgentBase(Agent):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        user_input_events: Tuple[Type[Event]],
        user_input_events_history_size: int | List[int],
        acceptability_trackers: Dict[str, TaskAcceptabilityTracker] = None,
    ):
        guidance_sensor = ActiveGuidanceSensor(subscribe_to=[*user_input_events])
        super().__init__([guidance_sensor, *sensors], actuators)
        self.beliefs = defaultdict(lambda: None)
        self._guidance_sensor = guidance_sensor
        self._acceptability_trackers: Dict[str, TaskAcceptabilityTracker] = (
            acceptability_trackers if acceptability_trackers else dict()
        )
        self._is_task_acceptable: Dict[str, bool] = defaultdict(dict)

        # set up buffer for storing user input events
        if isinstance(user_input_events_history_size, int):
            user_input_events_history_size = [user_input_events_history_size] * len(
                user_input_events
            )
        self._user_input_events = {
            t: deque(maxlen=hsize)
            for t, hsize in zip(user_input_events, user_input_events_history_size)
        }

    def get_latest_user_events(self, event_type: Type, n: int = 1) -> Iterator[Event]:
        # print(event_type, len(self._user_input_events[event_type]))
        try:
            return islice(self._user_input_events[event_type], 0, n)
        except IndexError:
            return None

    def __sense__(self, state, *args, **kwargs):
        for tracker in self._acceptability_trackers.values():
            self._guidance_sensor.sense_acceptability(tracker)
        return super().__sense__(state, *args, **kwargs)

    def on_error_observation(self, component: Component, observation: ErrorObservation):
        raise observation.exception()

    def __cycle__(self):
        # update beliefs from guidance sensor, if any other sensors are added in a subclass these should be handled explicitly in the subclass.
        for observation in self._guidance_sensor.iter_observations():
            if isinstance(observation, ErrorObservation):
                self.on_error_observation(self._guidance_sensor, observation)
            elif type(observation) in self._user_input_events:
                self._user_input_events[type(observation)].appendleft(observation)
            elif isinstance(observation, Observation):
                data = observation.values[0]
                try:
                    self.beliefs[data.pop("id")] = data
                except KeyError:
                    # pylint: disable=W0707:
                    raise ValueError(
                        f"Received observation: {observation} that doesn't contain an `id`."
                    )
            else:
                raise ValueError(
                    f"Received observation: {observation} of unknown type: {type(observation)}"
                )

        # check for errors in actuators
        for actuator in self.actuators:
            for observation in actuator.iter_observations():
                if isinstance(observation, ErrorObservation):
                    self.on_error_observation(actuator, observation)

        # update acceptability, TODO rework this a bit
        for task_id, tracker in self._acceptability_trackers.items():
            self._is_task_acceptable[task_id] = tracker.is_acceptable(self.beliefs)
