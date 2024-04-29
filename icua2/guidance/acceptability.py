from abc import ABC, abstractmethod
from typing import Dict, Any

from matbii.action import SetLightAction


class TaskAcceptabilityTracker(ABC):

    @abstractmethod
    def is_acceptable(self, beliefs: Dict[str, Any]):
        pass


class SystemMonitoringAcceptabilityTracker(TaskAcceptabilityTracker):

    def is_acceptable(self, beliefs: Dict[str, Any]):
        return (
            self.is_light_acceptable(1, beliefs)
            and self.is_light_acceptable(2, beliefs)
            and self.is_slider_acceptable(1, beliefs)
            and self.is_slider_acceptable(2, beliefs)
            and self.is_slider_acceptable(3, beliefs)
            and self.is_slider_acceptable(4, beliefs)
        )

    def is_slider_acceptable(self, _id: int, beliefs: Dict[str, Any]):
        # sliders should be at the center position (according to SetSliderAction.acceptable_state which is incs // 2 + 1)
        state = beliefs[slider_id(_id)]["data-state"]
        acceptable_state = beliefs[slider_incs_id(_id)]["incs"] // 2
        return state == acceptable_state

    def is_light_acceptable(self, _id: int, beliefs: Dict[str, Any]):
        return [self.is_light1_acceptable, self.is_light2_acceptable][_id - 1](beliefs)

    def is_light1_acceptable(self, beliefs: Dict[str, Any]):
        # light 1 should be on
        return beliefs[light_id(1)]["data-state"] == SetLightAction.ON

    def is_light2_acceptable(self, beliefs: Dict[str, Any]):
        # light 2 should be off
        return beliefs[light_id(2)]["data-state"] == SetLightAction.OFF


class TrackingAcceptabilityTracker(TaskAcceptabilityTracker):

    def is_acceptable(self, beliefs: Dict[str, Any]):
        return self.is_tracking_acceptable(beliefs)

    def is_tracking_acceptable(self, beliefs: Dict[str, Any]):
        target = beliefs[tracking_target_id()]
        box = beliefs[tracking_box_id()]
        target_top_left = (target["x"], target["y"])
        target_size = (target["width"], target["height"])
        box_top_left = (box["x"], box["y"])
        box_bottom_right = (
            box_top_left[0] + box["width"],
            box_top_left[1] + box["height"],
        )
        target_center = (
            target_top_left[0] + target_size[0] / 2,
            target_top_left[1] + target_size[1] / 2,
        )
        return TrackingAcceptabilityTracker.is_point_in_rectangle(
            target_center, box_top_left, box_bottom_right
        )

    @staticmethod
    def is_point_in_rectangle(point, rect_min, rect_max):
        px, py = point
        min_x, min_y = rect_min
        max_x, max_y = rect_max
        return min_x <= px <= max_x and min_y <= py <= max_y


class ResourceManagementAcceptabilityTracker(TaskAcceptabilityTracker):

    def is_acceptable(self, beliefs: Dict[str, Any]):
        return self.is_tank_acceptable("a", beliefs) and self.is_tank_acceptable(
            "b", beliefs
        )

    def is_tank_acceptable(self, _id: str, beliefs: Dict[str, Any]):
        tank = beliefs[tank_id(_id)]
        tank_level = beliefs[tank_level_id(_id)]

        fuel_capacity = tank["data-capacity"]
        fuel_level = tank["data-level"]
        acceptable_level = tank_level["data-level"] * fuel_capacity
        acceptable_range2 = (tank_level["data-range"] * fuel_capacity) / 2
        return (
            fuel_level >= acceptable_level - acceptable_range2
            and fuel_level <= acceptable_level + acceptable_range2
        )


def tank_id(tank: str):
    assert tank in ("a", "b")
    return f"tank-{tank}"


def tank_level_id(tank: str):
    assert tank in ("a", "b")
    return f"tank-{tank}-level"


def slider_id(slider: int):
    assert slider in (1, 2, 3, 4)
    return f"slider-{slider}-button-container"


def slider_incs_id(slider: int):
    assert slider in (1, 2, 3, 4)
    return f"slider-{slider}-incs"


def light_id(light: int):
    assert light in (1, 2)
    return f"light-{light}-button"


def tracking_box_id():
    return "tracking_box"


def tracking_target_id():
    return "tracking_target"
