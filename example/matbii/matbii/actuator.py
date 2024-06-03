# import re
# import time
# from functools import partial

# from star_ray.agent import Actuator, attempt
# from star_ray.event import MouseButtonEvent, MouseMotionEvent, KeyEvent, JoyStickEvent


# from ...utils import DEFAULT_KEY_BINDING  # TODO support other key bindings?

# DIRECTION_MAP = {
#     "up": (0, -1),
#     "down": (0, 1),
#     "left": (-1, 0),
#     "right": (1, 0),
# }
# # TODO this should be set in a config somewhere
# # this is measured in units per second and will be approximated based on the cycle time in TrackingActuator
# DEFAULT_TARGET_SPEED = 100


# class AvatarResourceManagementActuator(Actuator):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._get_pump_targets = partial(_get_click_targets, r"pump-([a-z]+)-button")

#     @attempt(route_events=[MouseButtonEvent])
#     def attempt_mouse_event(self, user_action: MouseButtonEvent):
#         assert isinstance(user_action, MouseButtonEvent)
#         # always include the user action as it needs to be logged
#         actions = [user_action]
#         if user_action.status == MouseButtonEvent.CLICK and user_action.button == 0:
#             actions.extend(self._get_pump_actions(user_action))
#         return actions

#     def _get_pump_actions(self, user_action):
#         targets = self._get_pump_targets(user_action.target)
#         return [TogglePumpAction(target=target) for target in targets]


# class AvatarSystemMonitoringActuator(Actuator):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._get_light_targets = partial(_get_click_targets, r"light-(\d+)-button")
#         self._get_slider_targets = partial(_get_click_targets, r"slider-(\d+)-button")

#     @attempt(route_events=[MouseButtonEvent])
#     def attempt_mouse_event(self, user_action: MouseButtonEvent):
#         assert isinstance(user_action, MouseButtonEvent)
#         # always include the user action as it needs to be logged
#         actions = [user_action]
#         if user_action.status == MouseButtonEvent.CLICK and user_action.button == 0:
#             actions.extend(self._get_light_actions(user_action))
#             actions.extend(self._get_slider_actions(user_action))
#         return actions

#     def _get_light_actions(self, user_action):
#         targets = [int(x) for x in self._get_light_targets(user_action.target)]
#         return [ToggleLightAction(target=target) for target in targets]

#     def _get_slider_actions(self, user_action):
#         targets = [int(x) for x in self._get_slider_targets(user_action.target)]
#         return [ResetSliderAction(target=target) for target in targets]


# def _get_click_targets(pattern, targets):
#     def _get():
#         for target in targets:
#             match = re.match(pattern, target)
#             if match:
#                 target = match.group(1)
#                 yield target

#     return list(_get())
