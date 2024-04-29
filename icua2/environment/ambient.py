from datetime import datetime
import pathlib

from typing import List, Dict, Any, Callable
from star_ray.agent import Agent, Actuator
from star_ray.event import (
    ErrorActiveObservation,
    MouseButtonEvent,
    KeyEvent,
    MouseMotionEvent,
)
from star_ray.plugin.xml import (
    XMLAmbient,
    xml_history,
    xml_change_tracker,
    xml_change_publisher,
    QueryXPath,
)
from ..utils import LOGGER, DEFAULT_XML_NAMESPACES, DEFAULT_SVG_PLACEHOLDER
from ..utils import TaskLoader, _Task, ICUAInternalError

# VALID_USER_ACTIONS = (MouseButtonEvent, KeyEvent, MouseMotionEvent)

# TODO move this to utils._const.py?

# use working directory instead?
_HISTORY_PATH = str(
    pathlib.Path(__package__).parent
    / "logs"
    / f"./history-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.h5"
)


@xml_history(use_disk=True, force_overwrite=False, path=_HISTORY_PATH)
@xml_change_publisher
@xml_change_tracker
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
        # TODO supply arguments to the loader... rather than relying on the default values
        # we are not making full use of it here (tasks can be enabled etc.)
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
        self.enable_dynamic_loading = enable_dynamic_loading
        self.suppress_warnings = suppress_warnings
        self._tasks: Dict[str, _Task] = dict()

    def register_task(
        self,
        name: str,
        path: str,
        agent_actuators: List[Callable[[], Actuator]] = None,
        avatar_actuators: List[Callable[[], Actuator]] = None,
    ):
        if name in self._tasks:
            raise ValueError(f"Task with name {name} already exists.")
        self._tasks[name] = self._task_loader.register_task(
            name,
            path,
            agent_actuators=agent_actuators,
            avatar_actuators=avatar_actuators,
            suppress_warnings=self.suppress_warnings,
            enable_dynamic_loading=self.enable_dynamic_loading,
        )

    def enable_task(self, task_name: str, insert_at: str = None):
        task = self._tasks[task_name]
        agent = task.new_agent()
        if agent:
            self.add_agent(agent)
        avatar = task.new_avatar()
        if avatar:
            self.add_agent(avatar)
        # update the task.html context? or the svg data ... which one is better?

    def disable_task(self, task_name: str):
        raise NotImplementedError()  # TODO

    def select(self, action):
        return super().__select__(action)

    def __select__(self, action):
        try:
            return super().__select__(action)
        except Exception as e:
            LOGGER.exception("Error occured during SELECT")
            return ErrorActiveObservation(exception=e, action_id=action)

    def __update__(self, action):
        try:
            return self._update_internal(action)
        except Exception as e:
            LOGGER.exception("Error occured during UPDATE")
            return ErrorActiveObservation(exception=e, action_id=action)

    def _update_internal(self, action):
        if isinstance(action, QueryXPath):
            return super().__update__(action)
        elif hasattr(action, "to_xml_queries"):  # TODO check a type its faster/clearer
            xml_actions = action.to_xml_queries(self.state)
            if isinstance(xml_actions, list | tuple):
                # some weirdness with list comprehension means super(MatbiiAmbient, self) is required...
                return [
                    super(MultiTaskAmbient, self).__update__(a) for a in xml_actions
                ]
            else:
                raise ICUAInternalError(
                    f"Ambient failed to convert action: `{action}` to XML queries, invalid return type: `{type(xml_actions)}`.",
                )
        # elif isinstance(action, VALID_USER_ACTIONS):
        #     # TODO log these actions somewhere...
        #     pass
        else:
            raise ICUAInternalError(
                f"Ambient received unknown action type: `{type(action)}`."
            )

    def __kill__(self):
        super().__kill__()
        # TODO flush the history to disk? - this should be implemented in the decorator
