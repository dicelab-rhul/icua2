from typing import Any
from collections.abc import Callable
import importlib.util
import inspect
import sys
import random
from lxml.etree import canonicalize
from jinja2 import Template
from functools import wraps
from pathlib import Path

from star_ray.utils import ValidatedEnvironment, TemplateLoader
from star_ray.agent import Agent, Actuator
from ._logging import LOGGER
from ._error import TaskConfigurationError
from ._schedule import ScheduledAgentFactory

__all__ = ("avatar_actuator", "agent_actuator", "TaskLoader")

EXT_SCHEMA = ".schema.json"
EXT_CONTEXT = ".json"
EXT_SCHEDULE = ".sch"
EXT_SVG = ".svg"
EXT_SVG_TEMPLATE = ".svg.jinja"
EXT_PY = ".py"

CLSATTR_IS_AVATAR_ACTUATOR = "__is_avatar_actuator__"
CLSATTR_IS_AGENT_ACTUATOR = "__is_agent_actuator__"


def avatar_actuator(cls: type[Actuator]):
    if not issubclass(cls, Actuator):
        raise TaskConfigurationError(
            f"Invalid use of @avatar, {cls} must derive `{Actuator.__name__}`"
        )
    setattr(cls, CLSATTR_IS_AVATAR_ACTUATOR, True)
    return cls


def agent_actuator(cls: type[Actuator]):
    if not issubclass(cls, Actuator):
        raise TaskConfigurationError(
            f"Invalid use of @agent, {cls} must derive `{Actuator.__name__}`"
        )
    setattr(cls, CLSATTR_IS_AGENT_ACTUATOR, True)
    return cls


class AvatarFactory:
    def __init__(self, actuators: list[type[Actuator] | Callable[[], Actuator]]):
        self._actuators = actuators

    def __call__(self, avatar: Agent):
        actuator_types = set(type(a) for a in avatar.get_actuators())
        for actuator in self._actuators:
            if actuator in actuator_types:
                raise ValueError(f"Avatar already has actuator of type: {actuator}.")
            avatar.add_component(actuator())
        return avatar


class Task:
    def __init__(
        self,
        task_name: str,
        task_template: Template,
        avatar_factory: Callable[[Agent], Agent],
        agent_factory: Callable[[], Agent],
    ):
        super().__init__()
        self._task_name = task_name
        self._task_template = task_template
        self._avatar_factory = avatar_factory
        self._agent_factory = agent_factory

    @property
    def task_name(self):
        return self._task_name

    def get_xml(self, context: dict[str, Any] | None = None) -> str:
        if context is None:
            context = dict()
        source = self._task_template.render(context)
        return canonicalize(source)

    def get_avatar(self, avatar: Agent) -> Agent:
        return self._avatar_factory(avatar)

    def get_agent(self) -> Agent | None:
        if self._agent_factory is None:
            return None
        return self._agent_factory()


class _DefaultFuncs:
    @staticmethod
    def min(*args):
        return min(args)

    @staticmethod
    def max(*args):
        return max(args)

    @staticmethod
    def uniform(a: int | float, b: int | float):
        if isinstance(a, int) and isinstance(b, int):
            return random.randint(a, b)
        return random.uniform(a, b)


class TaskLoader:
    def __init__(self):
        super().__init__()
        self._jinja_env = ValidatedEnvironment(
            loader=TemplateLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_schedule_functions(self):
        return [
            _DefaultFuncs.min,
            _DefaultFuncs.max,
            _DefaultFuncs.uniform,
        ]

    def register_task(self, name: str, path: str | list[str]) -> None:
        if isinstance(path, str | Path):
            path = [TaskLoader._path_normalise(path)]
        elif isinstance(path, list | tuple):
            path = [TaskLoader._path_normalise(p) for p in path]
        LOGGER.debug(f"Registering task: `{name}` at path(s): `{[p for p in path]}`")
        self._template_loader.add_namespace(name, path)

    def load(
        self,
        task_name: str,
        avatar_actuators: list[Actuator],
        agent_actuators: list[Actuator],
    ) -> Task:
        task_template = self.get_task_template(task_name=task_name)
        agent_factory = self.get_schedule(task_name, agent_actuators)
        avatar_factory = AvatarFactory(avatar_actuators)
        return Task(
            task_name=task_name,
            task_template=task_template,
            avatar_factory=avatar_factory,
            agent_factory=agent_factory,
        )

    def get_task_template(self, task_name: str) -> Template:
        files = self._get_task_files(task_name)
        state_path, _, _ = self._validate_state_files(files, task_name=task_name)
        return self._jinja_env.get_template(state_path.as_posix())

    def get_task_source(
        self, task_name: str, context: dict[str, Any] | None = None
    ) -> str:
        if context is None:
            context = dict()  # no additional context
        template: Template = self.get_task_template(task_name)
        return template.render(context)

    def get_schedule(
        self, task_name: str, actuators: list[type[Actuator]]
    ) -> Callable[[], Agent]:
        actuators = set(actuators)
        has_actuators = len(actuators) > 0
        files = self._get_task_files(task_name)
        schedule_path = files.get(EXT_SCHEDULE, None)
        if schedule_path:
            # TODO it would be nice if this could give the full path, its may be useful to see exactly which file is being loaded
            LOGGER.debug(f"loading schedule: {schedule_path.name}")
            # TODO perhaps we shouldnt load as a template... just load as text?
            # the templating syntax might interfere with things?
            source = self._jinja_env.get_template(schedule_path.as_posix()).render()
            agent_factory = ScheduledAgentFactory(
                source,
                actuators,
                self.get_schedule_functions(),
            )
            return agent_factory
        elif has_actuators:
            raise TaskConfigurationError(
                f"Configuration file: `{task_name}{EXT_SCHEDULE}` is missing for task: `{task_name}` but actuators: {actuators} were specified."
            )

    def _validate_state_files(
        self, files: dict[str, str], task_name: str
    ) -> tuple[Path, Path, Path]:
        state_path, context_path, schema_path = None, None, None
        if EXT_SVG in files:
            state_path = files[EXT_SVG]
            LOGGER.debug(f"loading state: `{state_path.name}`")
        elif EXT_SVG_TEMPLATE in files:
            state_path = files[EXT_SVG_TEMPLATE]
            LOGGER.debug(f"loading state: `{ state_path.name}` ")
            has_schema = EXT_SCHEMA in files
            has_context = EXT_CONTEXT in files
            if not has_context and not has_schema:
                raise TaskConfigurationError(
                    f"Configuration file: `{task_name}{EXT_CONTEXT}` is missing from task template: `{state_path.name}`."
                )
            elif not has_schema:
                LOGGER.warning(
                    f"validation schema: `{task_name}{EXT_SCHEMA}` is missing from task template: `{state_path.name}`",
                )

            if has_schema:
                schema_path = files[EXT_SCHEMA]
                LOGGER.debug(
                    f"with validator schema: `{schema_path.name}`",
                )
            if has_context:
                context_path = files[EXT_CONTEXT]
                LOGGER.debug(
                    f"with context: `{context_path.name}`",
                )
        else:
            raise TaskConfigurationError(
                f"State file: `{task_name}{EXT_SVG}(.jinja)` is missing for task: `{task_name}`."
            )
        return state_path, context_path, schema_path

    def _get_task_files(self, task_name: str):
        """Generator that gets all file paths associated with the given task."""

        def _gen():
            for file in self._template_loader.list_templates_in_namespace(task_name):
                file = task_name / Path(file)
                if file.stem.startswith(task_name):
                    yield "".join(file.suffixes), file

        return dict(_gen())

    @staticmethod
    def _path_normalise(path: str | Path) -> Path:
        return Path(path).expanduser().resolve().absolute().as_posix()

    @property
    def _template_loader(self) -> TemplateLoader:
        return self._jinja_env.loader

    # @LOGGER.indent
    # def load_actuators(
    #     self,
    #     task_name: str,
    #     paths: List[str],
    #     agent_actuators: List[Type[Actuator]] | None,
    #     avatar_actuators: List[Type[Actuator]] | None,
    #     enable_dynamic_loading: bool = False,
    #     suppress_warnings: bool = False,
    # ):
    #     LOGGER.debug("loading actuators:")
    #     if agent_actuators is None:
    #         agent_actuators = []
    #     if avatar_actuators is None:
    #         avatar_actuators = []
    #     if enable_dynamic_loading:
    #         for path in paths:
    #             actuator_classes, _ = load_task_package_from_path(
    #                 path, task_name, suppress_warnings=suppress_warnings
    #             )
    #             if not actuator_classes["agent"] and not actuator_classes["avatar"]:
    #                 raise TaskConfigurationError(
    #                     f"No actuator classes were found in task plugin, did you forget to tag with @{agent_actuator.__name__} or @{avatar_actuator.__name__}?"
    #                 )
    #             agent_actuators.extend(actuator_classes["agent"])
    #             avatar_actuators.extend(actuator_classes["avatar"])

    #     if agent_actuators:
    #         LOGGER.debug(
    #             LOGGER.format_iterable(agent_actuators, message="agent:", indent=True)
    #         )
    #     if avatar_actuators:
    #         LOGGER.debug(
    #             LOGGER.format_iterable(avatar_actuators, message="avatar:", indent=True)
    #         )

    #     return agent_actuators, avatar_actuators

    # def register_task(
    #     self,
    #     name: str,
    #     path: str | List[str],
    #     agent_actuators: List[Callable[[], Actuator]] = None,
    #     avatar_actuators: List[Callable[[], Actuator]] = None,
    #     enable_dynamic_loading: bool = False,
    # ) -> _Task:
    #     """Registers the given task. Loads relevant configuration files.

    #     Args:
    #         name (str): name of the task.
    #         path (str | List[str]): path (or paths) for the task configuration. If multiple paths are specified then files at the earlier paths will be prefered. This allows customisation and overriding of certain configuration files.
    #         agent_actuators (List[Callable[[], Actuator]], optional): classes to be used for agent actuators. Defaults to None.
    #         avatar_actuators (List[Callable[[], Actuator]], optional): classes to be used for avatar actuators. Defaults to None.
    #         enable_dynamic_loading (bool, optional): whether to dynamically load actuators from any `.py` files found in the task path(s). Defaults to False.

    #     Returns:
    #         Task: the configured task
    #     """
    #     if not isinstance(name, str):
    #         raise TypeError("Invalid argument `name`: must be of type `str`")
    #     if isinstance(path, str):
    #         path = [path]
    #     elif isinstance(path, Path):
    #         path = [path.as_posix()]
    #     elif isinstance(path, list):
    #         path = [Path(p).expanduser().resolve().absolute().as_posix() for p in path]
    #     else:
    #         raise TypeError(
    #             "Invalid argument `path`: must be of type `str` or `List[str]`"
    #         )
    #     LOGGER.debug("Registering task: `%s` at path(s): `%s`", name, [p for p in path])
    #     self._template_loader.add_namespace(name, path)
    #     # FILES: <TASK>.svg(.jinja), <TASK>.schema.json AND/OR <TASK>.json, <TASK>.sch
    #     files = self._get_task_files(name)
    #     # print(files)
    #     state = self.load_state(name, files)

    #     agent_actuators = (
    #         copy.deepcopy(agent_actuators) if agent_actuators is not None else []
    #     )
    #     avatar_actuators = (
    #         copy.deepcopy(avatar_actuators) if avatar_actuators is not None else []
    #     )

    #     # *.py (for dynamic loading)
    #     # TODO this should work the same as with config files - i.e. overriding the .py files.
    #     # Currently just loads .py files from all paths, overriding is not yet supported!
    #     # both sets of actuators are updated in the method call
    #     agent_actuators, avatar_actuators = self.load_actuators(
    #         name,
    #         path,
    #         agent_actuators,
    #         avatar_actuators,
    #         enable_dynamic_loading=enable_dynamic_loading,
    #     )

    #     agent_factory = self.load_schedule(
    #         name,
    #         files,
    #         agent_actuators,
    #     )
    #     return _Task(state, agent_factory, avatar_actuators)


def dont_write_bytecode(fun):
    # prevent __pycache__ from being created when dynamically importing
    @wraps(fun)
    def _dont(*args, **kwargs):
        old_dont_write = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        result = fun(*args, **kwargs)
        sys.dont_write_bytecode = old_dont_write
        return result

    return _dont


@dont_write_bytecode
def load_task_package_from_path(
    path: str | Path, task_name: str, suppress_warnings: bool = False
):
    path = Path(path).expanduser().resolve()
    module_name = f"_{task_name}"
    files = [
        Path(path).expanduser().resolve()
        for path in path.iterdir()
        if path.suffix == ".py"
    ]
    if not files:
        raise TaskConfigurationError(
            f"Failed to load task: `{task_name}`, no `.py` files were found in the task path: `{path}`"
        )
    if "__init__.py" in [path.name for path in files]:
        # load as a package...
        raise NotImplementedError("TODO allow loading task as a package")
    else:
        # load modules individually
        classes = []
        for file in files:
            LOGGER.debug(f"loading task plugin: `{file.name}`")
            classes.extend(_get_classes_from_file(file, f"{module_name}"))
        actuator_classes = _get_actuator_classes(
            classes, suppress_warnings=suppress_warnings
        )
        return actuator_classes, classes


def _get_actuator_classes(
    classes: list[type[Actuator]], suppress_warnings: bool = False
):
    actuators = {"avatar": [], "agent": []}
    for cls in classes:
        if issubclass(cls, Actuator):
            if getattr(cls, CLSATTR_IS_AGENT_ACTUATOR, False):
                actuators["agent"].append(cls)
            elif getattr(cls, CLSATTR_IS_AVATAR_ACTUATOR, False):
                actuators["avatar"].append(cls)
            elif not suppress_warnings:
                LOGGER.warning(
                    "An Actuator definition was found: `%s`, but it was not tagged as @%s or @%s.",
                    cls.__name__,
                    agent_actuator.__name__,
                    avatar_actuator.__name__,
                )
    return actuators


def _get_classes_from_file(file: str | Path, module_name: str):
    module = _get_module_from_file(file, module_name)
    classes = [
        member
        for _, member in inspect.getmembers(module)
        if inspect.isclass(member) and member.__module__ == module_name
    ]
    return classes


def _get_module_from_file(file: str | Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(file))
    if spec is not None:
        module = importlib.util.module_from_spec(spec)
        # sys.modules[module_name] = module  # Optional: Add to sys.modules if you want it globally available
        spec.loader.exec_module(module)
        return module
    else:
        raise ImportError(f"Failed to load task module from the given path: `{file}`")
