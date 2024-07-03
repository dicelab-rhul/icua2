from typing import List, Tuple, Any, Dict, Type
from star_ray.agent import Sensor, Actuator

from icua2.event import (
    Event,
    EyeMotionEvent,
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
)

from icua2.agent.guidance import GuidanceAgentBase as _GAB
from .acceptability import (
    TaskAcceptabilityTracker,
    TrackingAcceptabilityTracker,
    SystemMonitoringAcceptabilityTracker,
    ResourceManagementAcceptabilityTracker,
)
from .._const import (
    TASK_ID_RESOURCE_MANAGEMENT,
    TASK_ID_SYSTEM_MONITORING,
    TASK_ID_TRACKING,
)


class GuidanceAgentBase(_GAB):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        input_events: Tuple[Type[Event]] = (
            MouseButtonEvent,
            MouseMotionEvent,
            KeyEvent,
            EyeMotionEvent,
        ),
        input_events_history_size: int | List[int] = 100,
        acceptability_trackers: Dict[str, TaskAcceptabilityTracker] = None,
    ):
        # set acceptability tracker defaults
        if acceptability_trackers is None:
            acceptability_trackers = dict()
        acceptability_trackers.setdefault(
            TASK_ID_TRACKING, TrackingAcceptabilityTracker()
        )
        acceptability_trackers.setdefault(
            TASK_ID_RESOURCE_MANAGEMENT, ResourceManagementAcceptabilityTracker()
        )
        acceptability_trackers.setdefault(
            TASK_ID_SYSTEM_MONITORING, SystemMonitoringAcceptabilityTracker()
        )
        super().__init__(
            sensors=sensors,
            actuators=actuators,
            user_input_events=input_events,
            user_input_events_history_size=input_events_history_size,
            acceptability_trackers=acceptability_trackers,
        )

    @property
    def looking_at_elements(self) -> List[str]:
        try:
            return next(self.get_latest_user_events(EyeMotionEvent)).target
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
