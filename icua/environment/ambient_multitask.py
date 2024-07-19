from typing import Any, List, Dict, Callable
from star_ray.agent import Agent, Actuator
from star_ray.event import Event, ActiveObservation, ErrorActiveObservation
from star_ray_xml import insert
from star_ray_pygame import SVGAmbient

from ..event import EnableTask, DisableTask, RenderEvent, ShowGuidance, HideGuidance
from ..utils import TaskLoader, Task
from ..utils._logging import EventLogger


# these actions dont have an effect, but they are important for logging
INERT_ACTIONS = (RenderEvent, ShowGuidance, HideGuidance)


class MultiTaskAmbient(SVGAmbient):

    def __init__(
        self,
        avatar: Agent = None,
        agents: List[Agent] = None,
        logging_path: str = None,
        **kwargs,
    ):

        # this needs to happen before any call to __update__
        self._event_logger = None
        self._initialise_logging(logging_path=logging_path)
        # initialise agents
        agents = agents if agents else []
        agents.append(avatar)
        super().__init__(
            agents,
            **kwargs,
        )
        self._avatar = avatar
        self._task_loader = TaskLoader()
        self._tasks: Dict[str, Task] = dict()

    def _initialise_logging(self, logging_path: str = None):
        if logging_path:
            logging_file = EventLogger.default_log_path(
                path=logging_path, name="event_log_{datetime}.log"
            )
            # general event logging -- all calls to __update__ will trigger this logger
            self._event_logger = EventLogger(logging_file)

    def add_task(
        self,
        name: str,
        path: str,
        agent_actuators: List[Callable[[], Actuator]] = None,
        avatar_actuators: List[Callable[[], Actuator]] = None,
        enable: bool = False,
    ):
        if name in self._tasks:
            raise ValueError(f"Task with name {name} already exists.")
        self._task_loader.register_task(name, path)
        self._tasks[name] = self._task_loader.load(
            name, avatar_actuators=avatar_actuators, agent_actuators=agent_actuators
        )
        if enable:
            self.enable_task(name)

    def enable_task(
        self, task_name: str, context: Dict[str, Any] | None = None, insert_at: int = -1
    ):
        event = EnableTask(
            source=self.id, task_name=task_name, context=context, insert_at=insert_at
        )
        self.__update__(event)

    def disable_task(self, task_name: str):
        event = DisableTask(source=self.id, task_name=task_name)
        self.__update__(event)

    def rename_task(self, task_name, name):
        if task_name in self._tasks:
            if name in self._tasks:
                raise ValueError(
                    f"Failed to rename task: {task_name}, new name: {name} already exists."
                )
            self._tasks[name] = self._tasks[task_name]
            del self._tasks[task_name]
        else:
            raise ValueError(f"Failed to rename task: {task_name} as it doesn't exist.")

    def __update__(self, action: Event) -> ActiveObservation | ErrorActiveObservation:
        # always log the action immediately (before execution)
        self._event_logger.log(action)
        if isinstance(action, EnableTask):
            result = self._enable_task(action)
        elif isinstance(action, DisableTask):
            result = self._disable_task(action)
        elif isinstance(action, INERT_ACTIONS):
            # these actions have no effect but are important for experiment logging
            result = None
            print(action)
        else:
            result = super().__update__(action)
        return result

    def _disable_task(self, event: DisableTask):
        raise NotImplementedError("TODO")  # TODO

    def _enable_task(self, event: EnableTask):
        task = self._tasks[event.task_name]
        agent = task.get_agent()
        if agent:
            self.add_agent(agent)
        avatar = task.get_avatar(self._avatar)
        # this should not change... the task should only add relevant actuators
        assert self._avatar == avatar
        # default is to insert as the first child of the root
        return self.__update__(
            insert(
                xpath="/svg:svg",
                element=task.get_xml(event.context),
                index=event.insert_at,
            )
        )
