from typing import List
from lxml import etree
from pprint import pprint
from ast import literal_eval
from functools import partial

from star_ray.agent import Agent, Sensor, attempt
from star_ray.event import Event, ErrorActiveObservation, ActiveObservation
from star_ray.plugin.xml import SubscribeXMLElementChange, XMLElementChangeObservation
from star_ray.pubsub import Subscribe, Unsubscribe

from matbii.action import SetLightAction
from matbii.utils import _LOGGER

# TODO get this from the environment?
NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

from .acceptability import (
    light_id,
    slider_id,
    slider_incs_id,
    tracking_box_id,
    tracking_target_id,
    tank_id,
    tank_level_id,
)


class GuidanceSensor(Sensor):

    def __subscribe__(self):
        SUBSCRIBE_TO_ELEMENTS = []
        # interested in the state of the lights in the System Monitoring Task
        SUBSCRIBE_TO_ELEMENTS.extend([light_id(i) for i in (1, 2)])
        # interested in the state of the sliders in the System Monitoring Task
        SUBSCRIBE_TO_ELEMENTS.extend([slider_id(i) for i in (1, 2, 3, 4)])
        # interested in the number of slider increments so that the agent knows the acceptable state of each slider
        SUBSCRIBE_TO_ELEMENTS.extend([slider_incs_id(i) for i in (1, 2, 3, 4)])
        # interested in the state of the target in the Tracking Task, and the tracking box to determine the acceptable state
        SUBSCRIBE_TO_ELEMENTS.extend([tracking_target_id(), tracking_box_id()])
        # interested in the fuel levels of the main tanks in the Resource Management Task
        SUBSCRIBE_TO_ELEMENTS.extend([tank_id(i) for i in ("a", "b")])
        # also interested in the acceptable fuel levels in the Resource Management Task
        SUBSCRIBE_TO_ELEMENTS.extend([tank_level_id(i) for i in ("a", "b")])
        return [
            SubscribeXMLElementChange(topic=element_id)
            for element_id in SUBSCRIBE_TO_ELEMENTS
        ]


class GuidanceAgent(Agent):

    def __init__(self):
        super().__init__([GuidanceSensor()], [])
        self.beliefs = {}
        self._guidance_sensor: GuidanceSensor = next(iter(self.sensors))
        self._log_acceptable_states = None

    def __initialise__(self, state):
        # this will execute the subscription actions (see `GuidanceSensor`)
        super().__initialise__(state)
        # process initial observations (result of subscriptions) and update beliefs
        for observation in self._guidance_sensor.iter_observations():
            if observation.values:
                assert len(observation.values) == 1
                xml_element = etree.fromstring(observation.values[0])
                self.beliefs[xml_element.get("id")] = _get_xml_data(xml_element)
            else:
                pass  # TODO the element was not found...
                # perhaps the task was not enabled? check
        # self._log_acceptable_states = LogAcceptableState(self)

    def __cycle__(self):
        # with self._log_acceptable_states as logger:
        for observation in self._guidance_sensor.iter_observations():
            if isinstance(observation, XMLElementChangeObservation):
                # a change happened in an element of interest, update beliefs
                self.beliefs[observation.element_id].update(observation.values)
                # logger.log(observation.element_id)


def _literal_eval(v):
    try:
        return literal_eval(v)
    except:
        return v


def _get_xml_data(xml_element):
    data = dict({k: _literal_eval(v) for k, v in xml_element.attrib.items()})
    assert "children" not in data  # TODO children was used as an xml attribute? hmm...
    data["children"] = []
    for child in xml_element.getchildren():
        data["children"].append(_get_xml_data(child))
    return data


# class AcceptablilityTracker:

#     def __init__(self, agent: "GuidanceAgent"):
#         self.agent = agent
#         self._acceptable_funs = {
#             "light-1": partial(self.agent.is_light_acceptable, 1),
#             "light-2": partial(self.agent.is_light_acceptable, 2),
#             "slider-1": partial(self.agent.is_slider_acceptable, 1),
#             "slider-2": partial(self.agent.is_slider_acceptable, 2),
#             "slider-3": partial(self.agent.is_slider_acceptable, 3),
#             "slider-4": partial(self.agent.is_slider_acceptable, 4),
#             "tracking": self.agent.is_tracking_acceptable,
#             "tank-a": partial(self.agent.is_tank_acceptable, "a"),
#             "tank-b": partial(self.agent.is_tank_acceptable, "b"),
#         }
#         self._id_map = {
#             tracking_box_id(): "tracking",
#             tracking_target_id(): "tracking",
#             light_id(1): "light-1",
#             light_id(2): "light-2",
#             slider_id(1): "slider-1",
#             slider_id(2): "slider-2",
#             slider_id(3): "slider-3",
#             slider_id(4): "slider-4",
#             slider_incs_id(1): "slider-1",
#             slider_incs_id(2): "slider-2",
#             slider_incs_id(3): "slider-3",
#             slider_incs_id(4): "slider-4",
#             tank_id("a"): "tank-a",
#             tank_id("b"): "tank-b",
#             tank_level_id("a"): "tank-a",
#             tank_level_id("b"): "tank-b",
#         }
#         self._acceptable = {}
#         for k, v in self._acceptable_funs.items():
#             acceptable = v()
#             if not acceptable:
#                 _LOGGER.debug(
#                     "ACCEPTABLE UPDATE: %s is unacceptable.",
#                     k,
#                 )
#             self._acceptable[k] = acceptable

#         self._to_log = []
#         self._in = False

#     def __enter__(self):
#         self._in = True
#         return self

#     def log(self, element_id):
#         if not self._in:
#             raise ValueError(
#                 f"Invalid use of {LogAcceptableState}, `with` is required."
#             )
#         self._to_log.append(element_id)

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         for element_id in self._to_log:
#             k = self._id_map[element_id]
#             v = self._acceptable_funs[k]
#             was_acceptable = self._acceptable[k]
#             self._acceptable[k] = v()
#             if was_acceptable and not self._acceptable[k]:
#                 _LOGGER.debug(
#                     "ACCEPTABLE UPDATE: %s is unacceptable.",
#                     k,
#                 )
#             elif not was_acceptable and self._acceptable[k]:
#                 _LOGGER.debug(
#                     "ACCEPTABLE UPDATE: %s is acceptable.",
#                     k,
#                 )
#         self._in = False
#         self._to_log.clear()
#         return False
