"""Module contains the `MultiTaskAmbient` class, see class documentation for details."""

from typing import Any
from collections.abc import Callable
from star_ray.event import wrap_observation
from star_ray.agent import Agent, Actuator
from star_ray.event import Event, ActiveObservation, ErrorActiveObservation
from star_ray_xml import Insert, Select, XPathElementsNotFound
from star_ray_pygame import SVGAmbient

from ..event import (
    EyeMotionEvent,
    EyeMotionEventRaw,
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    ScreenSizeEvent,
)
from ..event import (
    EnableTask,
    DisableTask,
    RenderEvent,
    ShowGuidance,
    HideGuidance,
    TaskUnacceptable,
    TaskAcceptable,
)
from ..utils import TaskLoader, Task
from ..utils._logging import EventLogger


# these actions dont have an effect, but they are important for logging
INERT_ACTIONS = (
    RenderEvent,
    ShowGuidance,
    HideGuidance,
    TaskUnacceptable,
    TaskAcceptable,
)


class MultiTaskAmbient(SVGAmbient):
    """This class manages an SVG state and a collection of tasks that a user may want to interact with. It requires that a special agent the `Avatar` is provided which will act as an interface between the user and the environment. For details on what a `Task` is and how they are used see the `MultiTaskEnvironment` class documentation or read the `icua` wiki page on tasks (TODO provide a link to this)."""

    def __init__(
        self,
        avatar: Agent = None,
        agents: list[Agent] = None,
        svg_size: tuple[float, float] = None,
        svg_position: tuple[float, float] = None,
        logging_path: str = None,
        **kwargs,
    ):
        """Constructor.

        Args:
            avatar (Agent, optional): The users avatar. Defaults to None.
            agents (list[Agent], optional): list of initial agents. Defaults to None.
            svg_size (tuple[float, float], optional): size of the root SVG element, typically this should encompase the bounds of all tasks. Defaults to None, which will use the default `SVGAmbient.DEFAULT_SVG_SIZE`.
            svg_position (tuple[float, float], optional): position of the root SVG element in the UI window. Defaults to None, which which will use the default `SVGAmbient.DEFAULT_SVG_POSITION`.
            logging_path (str, optional): path that events will be logged to. Defaults to None  (see `MultiTaskAmbient` for details).
            kwargs (dict[str, Any]): Additional optional keyword arguments, see `SVGAmbient` for options.
        """
        # this needs to happen before any call to __update__
        self._event_logger = None
        self._initialise_logging(logging_path=logging_path)
        # initialise agents
        agents = agents if agents else []
        agents.append(avatar)
        super().__init__(
            agents,
            svg_size=svg_size,
            svg_position=svg_position,
            **kwargs,
        )
        self._avatar = avatar
        self._task_loader = TaskLoader()
        self._tasks: dict[str, Task] = dict()

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
        path: str | list[str],
        agent_actuators: list[Callable[[], Actuator]] | None = None,
        avatar_actuators: list[Callable[[], Actuator]] | None = None,
        enable: bool = False,
    ):
        """Add a new task, this will load all required files and prepare the task but will not start the task (unless `enable` is True). To start the task use `enable_task` or have an agent take the `EnableTask` action.

        Args:
            name (str): the unique name of the task.
            path (str | list[str]): path(s) to task files.
            agent_actuators (list[Callable[[], Actuator]] | None, optional): actuators with which to create agents from a schedule file, see `MultiTaskEnvironment` documentation for details. Defaults to None.
            avatar_actuators (list[Callable[[], Actuator]] | None, optional): actuators that will be added to the avatar upon enabling the task, see `MultiTaskEnvironment` documentation for details. Defaults to None.
            enable (bool, optional): whether to immediately enable the task. Defaults to False.
        """
        if name in self._tasks:
            raise ValueError(f"Task with name {name} already exists.")
        if agent_actuators is None:
            agent_actuators = []
        if avatar_actuators is None:
            avatar_actuators = []
        self._task_loader.register_task(name, path)
        self._tasks[name] = self._task_loader.load(
            name, avatar_actuators=avatar_actuators, agent_actuators=agent_actuators
        )
        if enable:
            self.enable_task(name)

    def enable_task(
        self, task_name: str, context: dict[str, Any] | None = None, insert_at: int = -1
    ):
        """Manually enable a task. Tasks may otherwise be enabled via an `EnableTask` action.

        Args:
            task_name (str): name of the task to enable.
            context (dict[str,Any]): context to use when enabling the task
            insert_at (int): at what position in the SVG tree to insert the task element.
        """
        event = EnableTask(
            source=self.id, task_name=task_name, context=context, insert_at=insert_at
        )
        result = self.__update__(event)
        if isinstance(result, ErrorActiveObservation):
            raise result.exception()

    def disable_task(self, task_name: str):
        """Manually disable a task. Tasks may otherwise be disabled via an `EnableTask` action.

        Args:
            task_name (str): name of the task to disable.
        """
        event = DisableTask(source=self.id, task_name=task_name)
        result = self.__update__(event)
        if isinstance(result, ErrorActiveObservation):
            raise result.exception()

    def rename_task(self, task_name: str, new_name: str) -> None:
        """Rename a task. If the task is enabled this will alter the `id` attribute of the task element (TODO).

        Args:
            task_name (str): current name of the task.
            new_name (str): new name of the task.
        """
        if task_name in self._tasks:
            if new_name in self._tasks:
                raise ValueError(
                    f"Failed to rename task: {task_name}, another take with name: {new_name} already exists."
                )
            task = self._tasks[new_name]
            self._tasks[task_name] = task
            task.task_name = new_name
            del self._tasks[task_name]
            # TODO update the name of the task element if it has been enabled!
        else:
            raise ValueError(f"Failed to rename task: {task_name} as it doesn't exist.")

    def __update__(self, action: Event) -> ActiveObservation | ErrorActiveObservation:  # noqa
        # always log the action immediately (before execution)
        if self._event_logger:
            self._event_logger.log(action)
        # execute the action here or in super()
        if isinstance(action, EnableTask):
            return self._enable_task(action)
        elif isinstance(action, DisableTask):
            return self._disable_task(action)
        elif isinstance(action, INERT_ACTIONS):
            # these actions have no effect but are important for experiment logging
            return None
        else:
            return super().__update__(action)

    def on_user_input_event(  # noqa
        self,
        action: EyeMotionEvent
        | EyeMotionEventRaw
        | MouseButtonEvent
        | MouseMotionEvent
        | KeyEvent
        | WindowCloseEvent
        | WindowOpenEvent
        | WindowFocusEvent
        | WindowMoveEvent
        | WindowResizeEvent
        | ScreenSizeEvent,
    ):
        return super().on_user_input_event(action)

    def is_task_enabled(self, task_name: str) -> bool:
        """Is the given task enabled? Specially, is the task element part of the state? This will search for an element with `id` equal to the name of the task.

        Note that if the `id` of the task element has been changed elsewherethen this will not give the expected result. This will not happen with correct use of `MultiTaskAmbient`.

        Args:
            task_name (str): name of the task to check.

        Returns:
            bool: True if the task is enabled (is part of the state), False otherwise.
        """
        try:
            result = self._state.select(
                Select.new(f"/svg:svg/*[@id='{task_name}']", ["id"])
            )
        except XPathElementsNotFound:
            return False
        return result is not None and len(result) > 0

    @wrap_observation
    def _disable_task(self, event: DisableTask):
        """Disables a task - this will be called when a `DisableTask` event is received."""
        raise NotImplementedError("TODO")  # TODO

    @wrap_observation
    def _enable_task(
        self, event: EnableTask
    ) -> ActiveObservation | ErrorActiveObservation:
        """Enables a task - this will be called when an `EnableTask` event is received."""
        task = self._tasks[event.task_name]
        # TODO this assumes that the id of the task is "task_name"!
        if self.is_task_enabled(event.task_name):
            raise ValueError(f"Task {event.task_name} is already enabled.")
        agent = task.get_agent()
        if agent:
            self.add_agent(agent)
        avatar = task.get_avatar(self._avatar)
        # this should not change... the task should only add relevant actuators
        assert self._avatar == avatar
        # default is to insert as the first child of the root
        # TODO we need to check what the task 'id' is to keep track of which tasks are enabled and active!
        return self.__update__(
            Insert(
                source=self.id,
                xpath="/svg:svg",
                element=task.get_xml(event.context),
                index=event.insert_at,
            )
        )
