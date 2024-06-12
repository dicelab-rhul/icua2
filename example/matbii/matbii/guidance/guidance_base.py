from typing import List, Tuple, Any, Dict
from lxml import etree
from ast import literal_eval
from collections import defaultdict, deque

from star_ray.agent import Agent, Component, Sensor, attempt
from star_ray.event import (
    Observation,
    ErrorObservation,
    MouseButtonEvent,
    KeyEvent,
    MouseMotionEvent,
)
from star_ray.pubsub import Subscribe
from star_ray_xml import select
from icua2.extras.eyetracking import EyeMotionEvent

EVENT_TYPES_USERINPUT = (MouseButtonEvent, MouseMotionEvent, KeyEvent, EyeMotionEvent)

from .acceptability import (
    TaskAcceptabilityTracker,
    ResourceManagementAcceptabilityTracker,
    SystemMonitoringAcceptabilityTracker,
    TrackingAcceptabilityTracker,
)
from .._const import (
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_TRACKING,
)


class ActiveGuidanceSensor(Sensor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @attempt
    def sense_acceptability(self, tracker: TaskAcceptabilityTracker):
        # continuously get data relevant for task acceptability
        # TODO this could be done using subscriptions if implement in XMLState (e.g. subscribe to changes for a particular element with an id)
        return tracker.select()

    @attempt
    def sense_element(self, element_id: str, *attrs):
        attrs = set(attrs)
        attrs.add("id")
        return select(xpath=f"//*[@id='{element_id}']", attrs=attrs)

    def __subscribe__(self):
        # subscribe to receive all user input events
        return [Subscribe(topic=event_type) for event_type in EVENT_TYPES_USERINPUT]


class GuidanceAgentBase(Agent):

    def __init__(
        self,
        eyetracking_history_size=200,
        mouse_motion_history_size=200,
        mouse_button_history_size=20,
        key_history_size=20,
    ):
        super().__init__([ActiveGuidanceSensor()], [])
        self.beliefs = defaultdict(lambda: None)
        self._guidance_sensor: ActiveGuidanceSensor = next(iter(self.sensors))
        self._trackers = {
            TASK_ID_RESOURCE_MANAGEMENT: ResourceManagementAcceptabilityTracker(),
            TASK_ID_SYSTEM_MONITORING: SystemMonitoringAcceptabilityTracker(),
            TASK_ID_TRACKING: TrackingAcceptabilityTracker(),
        }
        self._acceptable = defaultdict(dict)
        self._user_input = {
            EyeMotionEvent: deque(maxlen=eyetracking_history_size),
            MouseButtonEvent: deque(maxlen=mouse_motion_history_size),
            MouseMotionEvent: deque(maxlen=mouse_button_history_size),
            KeyEvent: deque(maxlen=key_history_size),
        }

    @property
    def looking_at_elements(self) -> List[str]:
        try:
            return self._user_input[EyeMotionEvent][0].target
        except IndexError:
            return []

    @property
    def mouse_at_elements(self) -> List[str]:
        try:
            return self._user_input[MouseMotionEvent][0].target
        except IndexError:
            return []

    @property
    def current_mouse_position(self) -> Dict[str, Any]:
        try:
            event = self._user_input[MouseMotionEvent][0]
            return dict(timestamp=event.timestamp, position=event.position)
        except IndexError:
            return None  # no mouse motion events were captured?

    @property
    def current_eye_position(self) -> Dict[str, Any]:
        try:
            event = self._user_input[EyeMotionEvent][0]
            return dict(timestamp=event.timestamp, position=event.position)
        except IndexError:
            return None

    def __sense__(self, state, *args, **kwargs):
        for tracker in self._trackers.values():
            self._guidance_sensor.sense_acceptability(tracker)
        return super().__sense__(state, *args, **kwargs)

    def handle_error_observation(
        self, component: Component, observation: ErrorObservation
    ):
        raise observation.exception()

    def __cycle__(self):
        # update beliefs from guidance sensor, if any other sensors are added in a subclass these should be handled explicitly in the subclass.
        for observation in self._guidance_sensor.iter_observations():
            if isinstance(observation, ErrorObservation):
                self.handle_error_observation(self._guidance_sensor, observation)
            elif isinstance(observation, EVENT_TYPES_USERINPUT):
                self._user_input[type(observation)].appendleft(observation)
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
                    self.handle_error_observation(actuator, observation)
        # update acceptability
        for task_id, tracker in self._trackers.items():
            self._acceptable[task_id].update(tracker.is_acceptable(self.beliefs))
