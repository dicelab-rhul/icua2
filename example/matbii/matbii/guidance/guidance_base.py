from typing import List, Tuple, Any, Dict
from lxml import etree
from ast import literal_eval
from collections import defaultdict, deque

from star_ray.agent import Agent, Sensor, attempt
from star_ray.event import (
    Observation,
    ErrorObservation,
    MouseButtonEvent,
    KeyEvent,
    MouseMotionEvent,
    EyeMotionEvent,
)
from star_ray.pubsub import Subscribe

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
        self.beliefs = {}
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

    def __cycle__(self):
        for observation in self._guidance_sensor.iter_observations():
            if isinstance(observation, ErrorObservation):
                # TODO handle the error properly?
                raise observation.exception()
            elif isinstance(observation, EVENT_TYPES_USERINPUT):
                self._user_input[type(observation)].appendleft(observation)
            elif isinstance(observation, Observation):
                data = observation.values[0]
                self.beliefs[data.pop("id")] = data
            else:
                raise ValueError(
                    f"Received observation: {observation} of unknown type: {type(observation)}"
                )

        for actuator in self.actuators:
            for observation in actuator.iter_observations():
                if isinstance(observation, ErrorObservation):
                    raise observation.exception()
        # update acceptability
        for task_id, tracker in self._trackers.items():
            self._acceptable[task_id].update(tracker.is_acceptable(self.beliefs))
