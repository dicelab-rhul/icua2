from typing import List, Tuple, Any, Dict, Type
from star_ray.agent import Sensor, Actuator
from star_ray.event import (
    Event,
    MouseButtonEvent,
    KeyEvent,
    MouseMotionEvent,
)
from icua2.extras.eyetracking import EyeMotionEvent
from icua2.agent.guidance import GuidanceAgentBase as _GAB

from .acceptability import TaskAcceptabilityTracker


class GuidanceAgentBase(_GAB):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        user_input_events: Tuple[Type[Event]] = (
            MouseButtonEvent,
            MouseMotionEvent,
            KeyEvent,
            EyeMotionEvent,
        ),
        user_input_events_history_size: int | List[int] = 100,
        acceptability_trackers: Dict[str, TaskAcceptabilityTracker] = None,
    ):
        # TODO use these as defaults?
        # if TASK_ID_RESOURCE_MANAGEMENT not in
        #     TASK_ID_RESOURCE_MANAGEMENT: ResourceManagementAcceptabilityTracker(),
        #     TASK_ID_SYSTEM_MONITORING: SystemMonitoringAcceptabilityTracker(),
        #     TASK_ID_TRACKING: TrackingAcceptabilityTracker(),
        # }

        super().__init__(
            sensors=sensors,
            actuators=actuators,
            user_input_events=user_input_events,
            user_input_events_history_size=user_input_events_history_size,
            acceptability_trackers=acceptability_trackers,
        )

    @property
    def looking_at_elements(self) -> List[str]:
        try:
            return next(self.get_latest_user_events(EyeMotionEvent, n=1)).target
        except StopIteration:
            return []

    @property
    def mouse_at_elements(self) -> List[str]:
        try:
            return next(self.get_latest_user_events(MouseMotionEvent)).target
        except StopIteration:
            return []

    @property
    def current_mouse_position(self) -> Dict[str, Any]:
        try:
            event = next(self.get_latest_user_events(MouseMotionEvent))
            return dict(timestamp=event.timestamp, position=event.position)
        except StopIteration:
            return None

    @property
    def current_eye_position(self) -> Dict[str, Any]:
        try:
            event = next(self.get_latest_user_events(EyeMotionEvent))
            return dict(timestamp=event.timestamp, position=event.position)
        except StopIteration:
            return None

    # def __sense__(self, state, *args, **kwargs):
    #     # TODO
    #     # for tracker in self._trackers.values():
    #     #     self._guidance_sensor.sense_acceptability(tracker)
    #     return super().__sense__(state, *args, **kwargs)
