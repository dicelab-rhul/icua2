from typing import List, Dict, Callable
from star_ray.event import ExitEvent
from star_ray.agent import Agent, Actuator
from star_ray_xml import XMLAmbient, insert, select, update

from ..utils import DEFAULT_XML_NAMESPACES, DEFAULT_SVG_PLACEHOLDER
from ..utils import TaskLoader, _Task, bounding_rectangle

from ..utils._logging import EventLogger


class MultiTaskAmbient(XMLAmbient):

    def __init__(
        self,
        agents: List[Agent] = None,
        xml: str = None,
        xml_namespaces: Dict[str, str] = None,
        enable_dynamic_loading: bool = False,
        suppress_warnings: bool = False,
        **kwargs,
    ):
        _namespaces = dict(**DEFAULT_XML_NAMESPACES)
        if xml_namespaces:
            _namespaces.update(xml_namespaces)
        super().__init__(
            agents if agents else [],
            xml=xml if xml else DEFAULT_SVG_PLACEHOLDER,
            namespaces=_namespaces,
            **kwargs,
        )
        self._task_loader = TaskLoader()
        self._enable_dynamic_loading = enable_dynamic_loading
        self.suppress_warnings = suppress_warnings
        self._tasks: Dict[str, _Task] = dict()

        self._logger = EventLogger(kwargs.get("event_log_path", None))

    def register_task(
        self,
        name: str,
        path: str,
        agent_actuators: List[Callable[[], Actuator]] = None,
        avatar_actuators: List[Callable[[], Actuator]] = None,
        enable: bool = False,
    ):
        if name in self._tasks:
            raise ValueError(f"Task with name {name} already exists.")
        self._tasks[name] = self._task_loader.register_task(
            name,
            path,
            agent_actuators=agent_actuators,
            avatar_actuators=avatar_actuators,
            suppress_warnings=self.suppress_warnings,
            enable_dynamic_loading=self._enable_dynamic_loading,
        )
        if enable:
            self.enable_task(name)

    def enable_task(self, task_name: str):
        task = self._tasks[task_name]
        agent = task.get_agent()
        if agent:
            self.add_agent(agent)
        # default is to insert as the first child of the root
        self.__update__(insert(xpath="/svg:svg", element=task.get_xml(), index=0))
        # update the bounding rectangle of the root svg... this is default behaviour TODO an option for this...
        bounds = list(
            self.__select__(
                select(xpath="/svg:svg/svg:svg", attrs=["x", "y", "width", "height"])
            ).values
        )
        bounds.append(dict(x=0, y=0, width=0, height=0))

        # # TODO validate bounds
        brect = bounding_rectangle(bounds)
        self.__update__(
            update(
                xpath="/svg:svg",
                attrs=dict(width=brect["width"], height=brect["height"]),
            )
        )
        # TODO log enabled task

    def disable_task(self, task_name: str):
        raise NotImplementedError()  # TODO
        # TODO log enabled task

    def __update__(self, action):
        # log actions
        if isinstance(action, ExitEvent):
            self.__kill__()
        result = super().__update__(action)
        # TODO check for errors before logging...
        self._logger.log(action)
        return result

    # def _update_internal(self, action):
    #     if isinstance(action, QueryXPath):
    #         return super().__update__(action)
    #     elif hasattr(action, "to_xml_queries"):  # TODO check a type its faster/clearer
    #         xml_actions = action.to_xml_queries(self.state)
    #         if isinstance(xml_actions, list | tuple):
    #             # some weirdness with list comprehension means super(MatbiiAmbient, self) is required...
    #             return [
    #                 super(MultiTaskAmbient, self).__update__(a) for a in xml_actions
    #             ]
    #         else:
    #             raise ICUAInternalError(
    #                 f"Ambient failed to convert action: `{action}` to XML queries, invalid return type: `{type(xml_actions)}`.",
    #             )
    #     # elif isinstance(action, VALID_USER_ACTIONS):
    #     #     # TODO log these actions somewhere...
    #     #     pass
    #     else:
    #         raise ICUAInternalError(
    #             f"Ambient received unknown action type: `{type(action)}`."
    #         )

    def __kill__(self):
        super().__kill__()
        # TODO flush the history to disk? - this should be implemented in the decorator
