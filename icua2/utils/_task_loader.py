from typing import Dict, Set, List, Tuple, Any, Type, Callable
import importlib.util
import inspect
import sys
import copy
from jinja2 import Template
from functools import wraps
from pathlib import Path
from lxml import etree

from star_ray.utils import ValidatedEnvironment, TemplateLoader
from star_ray.agent import Actuator
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


def avatar_actuator(cls: Type[Actuator]):
    if not issubclass(cls, Actuator):
        raise TaskConfigurationError(
            f"Invalid use of @avatar, {cls} must derive `{Actuator.__name__}`"
        )
    setattr(cls, CLSATTR_IS_AVATAR_ACTUATOR, True)
    return cls


def agent_actuator(cls: Type[Actuator]):
    if not issubclass(cls, Actuator):
        raise TaskConfigurationError(
            f"Invalid use of @agent, {cls} must derive `{Actuator.__name__}`"
        )
    setattr(cls, CLSATTR_IS_AGENT_ACTUATOR, True)
    return cls


class _Task:

    def __init__(self, state: Template, agent_factory: Any, avatar_actuators: Any):
        self._state = state
        self._agent_factory = agent_factory if agent_factory else lambda: None
        self._avatar_actuators = avatar_actuators if avatar_actuators else []

    def get_agent(self):
        return self._agent_factory()

    def get_avatar_actuators(self):
        return self._avatar_actuators

    def get_xml(self, context: Dict[str, Any] = None):
        if context is None:
            context = dict()
        return etree.canonicalize(self._state.render(context))


class _DefaultFuncs:
    @staticmethod
    def min(*args):
        return min(args)

    @staticmethod
    def max(*args):
        return max(args)


class TaskLoader:

    def __init__(self):
        super().__init__()
        self._jinja_env = ValidatedEnvironment(
            loader=TemplateLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def register_task(
        self,
        name: str,
        path: str | List[str],
        agent_actuators: List[Callable[[], Actuator]] = None,
        avatar_actuators: List[Callable[[], Actuator]] = None,
        enable_dynamic_loading: bool = False,
        suppress_warnings: bool = False,
    ) -> _Task:
        """Registers the given task. Loads relevant configuration files.

        Args:
            name (str): name of the task.
            path (str | List[str]): path (or paths) for the task configuration. If multiple paths are specified then files at the earlier paths will be prefered. This allows customisation and overriding of certain configuration files.
            agent_actuators (List[Callable[[], Actuator]], optional): classes to be used for agent actuators. Defaults to None.
            avatar_actuators (List[Callable[[], Actuator]], optional): classes to be used for avatar actuators. Defaults to None.
            enable_dynamic_loading (bool, optional): whether to dynamically load actuators from any `.py` files found in the task path(s). Defaults to False.
            suppress_warnings (bool, optional): whether to supress warnings. Defaults to False.

        Returns:
            Task: the configured task
        """
        if isinstance(path, (str, Path)):
            path = [path]
        path = [Path(p).expanduser().resolve().absolute() for p in path]
        LOGGER.debug(
            "Registering task: `%s` at path(s): `%s`", name, [str(p) for p in path]
        )
        self._template_loader.add_namespace(name, path)
        # FILES
        # <TASK>.svg(.jinja)
        # <TASK>.schema.json AND/OR <TASK>.json
        # <TASK>.sch
        files = self._get_task_files(name, suppress_warnings=suppress_warnings)
        state = self.load_state(name, files, suppress_warnings=suppress_warnings)

        agent_actuators = (
            copy.deepcopy(agent_actuators) if not agent_actuators is None else []
        )
        avatar_actuators = (
            copy.deepcopy(avatar_actuators) if not avatar_actuators is None else []
        )

        # *.py (for dynamic loading)
        # TODO this should work the same as with config files - i.e. overriding the .py files.
        # Currently just loads .py files from all paths, overriding is not yet supported!
        for p in path:
            # both sets of actuators are updated in the method call
            self.load_actuators(
                name,
                p,
                agent_actuators,
                avatar_actuators,
                enable_dynamic_loading=enable_dynamic_loading,
                suppress_warnings=suppress_warnings,
            )

        agent_factory = self.load_schedule(
            name,
            files,
            agent_actuators,
            suppress_warnings=suppress_warnings,
        )
        return _Task(state, agent_factory, avatar_actuators)

    def load_state(
        self, task_name: str, files: Dict[str, str], suppress_warnings: bool = False
    ) -> Template:
        state_path, _, _ = self._validate_state_files(
            files, task_name=task_name, suppress_warnings=suppress_warnings
        )
        # this template contains all required information about the context and schema files,
        # and will validate any additional context automatically
        return self._jinja_env.get_template(str(state_path))

    def load_actuators(
        self,
        task_name: str,
        path: str,
        agent_actuators: List[Type[Actuator]] | None,
        avatar_actuators: List[Type[Actuator]] | None,
        enable_dynamic_loading: bool = False,
        suppress_warnings: bool = False,
    ):
        if agent_actuators is None:
            agent_actuators = []
        if avatar_actuators is None:
            avatar_actuators = []
        if enable_dynamic_loading:
            actuator_classes, _ = load_task_package_from_path(
                path, task_name, suppress_warnings=suppress_warnings
            )
            if not actuator_classes["agent"] and not actuator_classes["avatar"]:
                raise TaskConfigurationError(
                    f"No actuator classes were found in task plugin, did you forget to tag with @{agent_actuator.__name__} or @{avatar_actuator.__name__}?"
                )
            agent_actuators.extend(actuator_classes["agent"])
            avatar_actuators.extend(actuator_classes["avatar"])
        with LOGGER.indent:
            if agent_actuators:
                LOGGER.debug(
                    LOGGER.format_iterable(
                        agent_actuators, message=" agent@", indent=True
                    )
                )
            if avatar_actuators:
                LOGGER.debug(
                    LOGGER.format_iterable(
                        avatar_actuators, message="avatar@", indent=True
                    )
                )
        return agent_actuators, avatar_actuators

    def get_default_funcs(self):
        from random import randint, uniform

        return [_DefaultFuncs.min, _DefaultFuncs.max, randint, uniform]

    @LOGGER.indent
    def load_schedule(
        self,
        task_name: str,
        files: Dict[str, str],
        agent_actuators: List[Type[Actuator]] | None,
        suppress_warnings: bool = False,
    ):
        # is the task static? (i.e. is there an agent that will be updating the task)
        schedule_path = self._validate_schedule_files(
            files,
            task_name=task_name,
            suppress_warnings=suppress_warnings,
            runtime_actions=len(agent_actuators) > 0,
        )
        if schedule_path:
            # TODO it would be nice if this could give the full path, its may be useful to see exactly which file is being loaded
            LOGGER.debug("loading schedule: `%s`", schedule_path.name)
            # TODO perhaps we shouldnt load as a template... just load as text?
            # the templating syntax might interfere with things?
            schedule_source = self._jinja_env.get_template(str(schedule_path)).render()
            with LOGGER.indent:
                # print(agent_actuators)
                agent_factory = ScheduledAgentFactory(
                    schedule_source, agent_actuators, self.get_default_funcs()
                )
            return agent_factory
        else:
            return None

    def _validate_schedule_files(
        self,
        files: Dict[str, str],
        task_name: str,
        runtime_actions=False,
        suppress_warnings: bool = False,
    ):
        if not EXT_SCHEDULE in files and runtime_actions:
            raise TaskConfigurationError(
                f"Configuration file: `{task_name}{EXT_SCHEDULE}` is missing for task: `{task_name}`"
            )
        elif EXT_SCHEDULE in files and not runtime_actions:
            raise TaskConfigurationError(
                f"Found schedule configuration file: `{files[EXT_SCHEDULE].name}` but no actions were found."
            )
        schedule_path = files.get(EXT_SCHEDULE, None)
        if not schedule_path:
            LOGGER.debug(
                "No schedule file: `%s.%s` was found.", task_name, EXT_SCHEDULE
            )
        return schedule_path

    @LOGGER.indent
    def _validate_state_files(
        self, files: Dict[str, str], task_name: str, suppress_warnings: bool = False
    ):
        state_path, context_path, schema_path = None, None, None
        # check that state files exist
        if EXT_SVG in files:
            state_path = files[EXT_SVG]
            LOGGER.debug("loading state: `%s`", state_path.name)
        elif EXT_SVG_TEMPLATE in files:
            state_path = files[EXT_SVG_TEMPLATE]
            LOGGER.debug("loading state: `%s` ", state_path.name)
            with LOGGER.indent:
                has_schema = EXT_SCHEMA in files
                has_context = EXT_CONTEXT in files
                if not has_context and not has_schema:
                    raise TaskConfigurationError(
                        f"Configuration file: `{task_name}{EXT_CONTEXT}` is missing from task template: `{state_path.name}`."
                    )
                elif not has_schema and not suppress_warnings:
                    LOGGER.warning(
                        "validation schema: `%s%s` is missing from task template: `%s`",
                        task_name,
                        EXT_SCHEMA,
                        state_path.name,
                    )

                if has_schema:
                    schema_path = files[EXT_SCHEMA]
                    LOGGER.debug("with validator schema: `%s`", schema_path.name)
                if has_context:
                    context_path = files[EXT_CONTEXT]
                    LOGGER.debug("with context: `%s`", context_path.name)
        else:
            raise TaskConfigurationError(
                f"State file: `{task_name}{EXT_SVG}(.jinja)` is missing for task: `{task_name}`."
            )
        return state_path, context_path, schema_path

    def _get_task_files(self, task_name: str, suppress_warnings: bool = False):
        def _gen():
            for file in self._template_loader.list_templates_in_namespace(task_name):
                file = task_name / Path(file)
                if file.stem.startswith(task_name):
                    yield "".join(file.suffixes), file

        return dict(_gen())

    @property
    def _template_loader(self) -> TemplateLoader:
        return self._jinja_env.loader


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
            LOGGER.debug("  loading task plugin: `%s`", file.name)
            classes.extend(_get_classes_from_file(file, f"{module_name}"))
        actuator_classes = _get_actuator_classes(
            classes, suppress_warnings=suppress_warnings
        )
        return actuator_classes, classes


def _get_actuator_classes(
    classes: List[Type[Actuator]], suppress_warnings: bool = False
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
