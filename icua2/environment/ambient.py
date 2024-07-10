from typing import Any, List, Dict, Callable, Tuple
from star_ray.agent import Agent, Actuator
from star_ray.pubsub import EventPublisher, Subscribe, Unsubscribe
from star_ray.event import ActiveObservation, ErrorActiveObservation
from star_ray_xml import (
    XMLAmbient,
    insert,
    update,
    Update,
    Insert,
    Delete,
    Replace,
)

from ..event import (
    TaskDisabledEvent,
    TaskEnabledEvent,
    EnableTask,
    DisableTask,
    EyeMotionEvent,
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
)
from ..utils import DEFAULT_XML_NAMESPACES, DEFAULT_SVG_PLACEHOLDER
from ..utils import TaskLoader
from ..utils._task_loader import _Task
from ..utils._logging import EventLogger, LOGGER

EVENT_TYPES_USERINPUT = (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    EyeMotionEvent,
)
EVENT_TYPES_XML = (Update, Insert, Delete, Replace)

SUBSCRIPTION_EVENTS = set(
    EventPublisher.fully_qualified_name(t) for t in EVENT_TYPES_USERINPUT
)
SUBSCRIPTION_XML_EVENTS = set(
    EventPublisher.fully_qualified_name(t) for t in EVENT_TYPES_XML
)


class MultiTaskAmbient(XMLAmbient):

    def __init__(
        self,
        agents: List[Agent] = None,
        svg: str = None,
        namespaces: Dict[str, str] = None,
        enable_dynamic_loading: bool = False,
        svg_size: Tuple[float, float] = None,
        svg_position: Tuple[float, float] = None,
        logging_path: str = None,
        **kwargs,
    ):
        _namespaces = dict(**DEFAULT_XML_NAMESPACES)
        if namespaces:
            _namespaces.update(namespaces)
        super().__init__(
            agents if agents else [],
            xml=svg if svg else DEFAULT_SVG_PLACEHOLDER,
            namespaces=_namespaces,
            **kwargs,
        )
        self._task_loader = TaskLoader()
        self._enable_dynamic_loading = enable_dynamic_loading
        self._tasks: Dict[str, _Task] = dict()
        # initialise various loggers
        self._logger_event = None
        self._logger_xml_event = None
        self._initialise_logging(logging_path)
        # publisher will notify agents of user events
        self._event_publisher = EventPublisher()
        self._padding = kwargs.get("padding", 10)
        # self._kill_callback = None

        # set values for the root container
        root_attributes = {}
        if svg_size:
            assert len(svg_size) == 2
            root_attributes["width"] = svg_size[0]
            root_attributes["height"] = svg_size[1]
        if svg_position:
            root_attributes["x"] = svg_position[0]
            root_attributes["y"] = svg_position[1]
        self.__update__(update(xpath="/svg:svg", attrs=root_attributes))

        # otherwise we can get some confusing rendering errors... (blank canvas)
        assert self._state.get_root().get("x", None) is not None
        assert self._state.get_root().get("y", None) is not None

    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:
        if action.topic in SUBSCRIPTION_EVENTS:
            if isinstance(action, Subscribe):
                self._event_publisher.subscribe(
                    action.topic, action.subscriber)
            elif isinstance(action, Unsubscribe):
                self._event_publisher.unsubscribe(
                    action.topic, action.subscriber)
        elif action.topic in SUBSCRIPTION_XML_EVENTS:
            return super().__subscribe__(action)
        else:
            raise ValueError(
                f"Received invalid subscription, unknown topic: {action.topic}"
            )

    def _initialise_logging(self, logging_path: str):
        # initialise logging, log to two files:
        # 1. high level events + user input - these are higher level events triggered by the user or agents which will lead to some underlying state update (via their execute method)
        # 2. xml events - these are "raw" updates to the underlying state
        loggin_file = EventLogger.default_log_path(
            path=logging_path, name="event_log_{datetime}.log"
        )
        self._logger_event = EventLogger(loggin_file)
        self._logger_xml_event = EventLogger(
            loggin_file.with_name(
                loggin_file.name.replace("event_log", "event_log_xml")
            )
        )
        self._state.subscribe(Update, subscriber=self._logger_xml_event)
        self._state.subscribe(Insert, subscriber=self._logger_xml_event)
        self._state.subscribe(Delete, subscriber=self._logger_xml_event)
        self._state.subscribe(Replace, subscriber=self._logger_xml_event)

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
            enable_dynamic_loading=self._enable_dynamic_loading,
        )
        if enable:
            self.enable_task(name)

    def rename_task(self, task_name, name):
        """Rename an existing task.

        Args:
            task_name (_type_): _description_
            name (_type_): _description_

        Raises:
            ValueError: _description_
            ValueError: _description_
        """
        if task_name in self._tasks:
            if name in self._tasks:
                raise ValueError(
                    f"Failed to rename task: {task_name}, new name: {name} already exists."
                )
            self._tasks[name] = self._tasks[task_name]
            del self._tasks[task_name]
        else:
            raise ValueError(
                f"Failed to rename task: {task_name} as it doesn't exist.")

    def enable_task(
        self, task_name: str, context: Dict[str, Any] = None, insert_at: int = -1
    ):
        task = self._tasks[task_name]
        agent = task.get_agent()
        if agent:
            self.add_agent(agent)
            # check if the agent has already been initialised...
        # default is to insert as the first child of the root
        self._state.insert(
            insert(xpath="/svg:svg", element=task.get_xml(context), index=insert_at)
        )
        event = TaskEnabledEvent(task_name=task_name)
        self._event_publisher.notify_subscribers(event)

    def disable_task(self, task_name: str):
        raise NotImplementedError()  # TODO

    def __update__(self, action):
        result = None
        if isinstance(action, EVENT_TYPES_USERINPUT):
            self._event_publisher.notify_subscribers(action)
        elif isinstance(action, EnableTask):
            self.enable_task(
                action.task_name, context=action.context, insert_at=action.insert_at
            )
        elif isinstance(action, DisableTask):
            self.disable_task(action.task_name)
        else:
            result = super().__update__(action)

        # TODO check for errors before logging...
        self._logger_event.log(action)

        if isinstance(action, WindowCloseEvent):
            # TODO this will wait for all agents to finish, which might take awhile, we should cancel coroutines,
            # the agent loops are handled in the environment... so what is the best way to do this?
            LOGGER.debug("Window closed: %s, shutting down...", action)
            self._is_alive = False  # trigger termination
        return result
