import pathlib
from typing import Any, List, Dict, Callable, Type
from star_ray.event import (
    ActiveObservation,
    ErrorActiveObservation,
    Event,
    ExitEvent,
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    JoyStickEvent,
    EyeMotionEvent,
)
from star_ray.agent import Agent, Actuator
from star_ray.pubsub._pubsub import Subscriber
from star_ray_xml import (
    XMLAmbient,
    insert,
    select,
    update,
    Update,
    Insert,
    Delete,
    Replace,
    Expr,
)
from star_ray.pubsub import EventPublisher, Subscribe, Unsubscribe
from ..utils import DEFAULT_XML_NAMESPACES, DEFAULT_SVG_PLACEHOLDER
from ..utils import TaskLoader, _Task, bounding_rectangle
from ..utils._logging import EventLogger


EVENT_TYPES_USERINPUT = (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    JoyStickEvent,
    EyeMotionEvent,
)
EVENT_TYPES_XML = (Update, Insert, Delete, Replace)

SUBSCRIPTION_EVENTS = set(
    EventPublisher.fully_qualified_name(t)
    for t in (ExitEvent, *EVENT_TYPES_USERINPUT)
    # TODO eye tracking event?
)
SUBSCRIPTION_XML_EVENTS = set(
    EventPublisher.fully_qualified_name(t) for t in EVENT_TYPES_XML
)


class TaskEnabledEvent(Event):
    task_name: str


class TaskDisabledEvent(Event):
    task_name: str


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
        # initialise various loggers
        self._logger_event = None
        self._logger_xml_event = None
        self._initialise_logging(**kwargs)
        # publisher with will notify on user events
        self._event_publisher = EventPublisher()
        self._padding = kwargs.get("padding", 10)

    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:

        if action.topic in SUBSCRIPTION_EVENTS:
            if isinstance(action, Subscribe):
                self._event_publisher.subscribe(action.topic, action.subscriber)
            elif isinstance(action, Unsubscribe):
                self._event_publisher.unsubscribe(action.topic, action.subscriber)
        elif action.topic in SUBSCRIPTION_XML_EVENTS:
            return super().__subscribe__(action)
        else:
            raise ValueError(
                f"Received invalid subscription, unknown topic: {action.topic}"
            )

    def _initialise_logging(self, **kwargs):
        # initialise logging, we log to two files:
        # 1. high level events + user input - these are higher level events triggered by the user or agents which will lead to some underlying state update (via their execute method)
        # 2. xml events - these are "raw" updates to the underlying state
        self._logger_event = EventLogger(
            kwargs.get(
                "log_path_event",
                EventLogger.default_log_path(name="event_log_{datetime}.log"),
            )
        )
        self._logger_xml_event = EventLogger(
            kwargs.get(
                "log_path_event_xml",
                EventLogger.default_log_path(name="event_log_xml_{datetime}.log"),
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
        self._state.insert(insert(xpath="/svg:svg", element=task.get_xml(), index=0))

        # update the bounding rectangle of the root svg... this is default behaviour TODO an option for this...
        # also adds some padding around tasks...
        bounds = list(
            self._state.select(
                select(xpath="/svg:svg/svg:svg", attrs=["x", "y", "width", "height"])
            )
        )
        bounds.append(dict(x=0, y=0, width=0, height=0))
        # # TODO validate bounds
        brect = bounding_rectangle(bounds)
        self._state.update(
            update(
                xpath="/svg:svg/svg:svg",
                attrs=dict(
                    x=Expr("{value}+{padding}", padding=self._padding),
                    y=Expr("{value}+{padding}", padding=self._padding),
                ),
            )
        )
        self._state.update(
            update(
                xpath="/svg:svg",
                attrs=dict(
                    width=brect["width"] + self._padding * 2,
                    height=brect["height"] + self._padding * 2,
                ),
            )
        )
        self._logger_event.log(TaskEnabledEvent(task_name=task_name))

    def disable_task(self, task_name: str):
        raise NotImplementedError()  # TODO
        self._logger_event.log(TaskDisabledEvent(task_name=task_name))

    def __update__(self, action):
        result = None
        if isinstance(action, EVENT_TYPES_USERINPUT):
            self._event_publisher.notify_subscribers(action)
        elif isinstance(action, ExitEvent):
            self.__kill__()
        else:
            result = super().__update__(action)
        # TODO check for errors before logging...
        self._logger_event.log(action)
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
