import sys
import aiostream
import itertools
from typing import List, Dict, Callable, Set, Type, Any
from types import MethodType
from star_ray import Agent, Actuator
from pyfuncschedule import parser as schedule_parser, Schedule, ScheduleParser
from ._logging import LOGGER
from ._error import TaskConfigError


class ScheduledAgent(Agent):
    """The actions of this agent are determined by a fixed schedule that is provided upon creation. The schedule is a collection of `attempts` that are part of the given actuators."""

    def __init__(self, actuators: List[Actuator], schedules: List[Schedule]):
        super().__init__([], actuators)
        self._schedules = [sch.stream() for sch in schedules]
        self._iter_context = None  # set on initialise
        self._iter_schedules = None  # set on initialise

    async def __initialise__(self):
        self._iter_context = aiostream.stream.merge(*self._schedules).stream()
        self._iter_schedules = await self._iter_context.__aenter__()

    async def __cycle__(self):
        try:
            # this will await the next action from the collection of schedules
            await self._iter_schedules.__anext__()
        except StopAsyncIteration:
            await self._iter_context.__aexit__(None, None, None)
        except Exception:  # pylint: disable=W0718
            exc_type, exc_val, exc_tb = sys.exc_info()
            await self._iter_context.__aexit__(exc_type, exc_val, exc_tb)

    async def __sense__(self, state, *args, **kwargs):
        return super().__sense__(state, *args, **kwargs)

    async def __execute__(self, state, *args, **kwargs):
        return super().__execute__(state, *args, **kwargs)

    async def __kill__(self):
        await self._iter_context.aclose()


class ScheduledAgentFactory:

    def __init__(
        self,
        schedule_source: str,
        actuator_types: Set[Type[Actuator]],
        funcs: List[Callable],
    ):
        super().__init__()
        self._source = schedule_source
        self._actuator_types: Set[Type[Actuator]] = actuator_types
        self._functions: Dict[str, Callable] = {fun.__name__: fun for fun in funcs}
        self._parse_result: Any = None  # TODO type hint...
        self.parse_schedule()

    def parse_schedule(
        self,
    ):
        parser = ScheduleParser()
        for name, fun in self._functions.items():
            parser.register_function(fun, name=name)
            LOGGER.debug("registered function: %s", name)

        self._attempts = dict()
        for cls, action in self._get_all_attempt_methods(self._actuator_types):
            parser.register_action(action)
            LOGGER.debug(
                "registered attempt: %s@%s",
                cls.__name__,
                action.__name__,
            )
        try:
            self._parse_result = parser.parse(self._source)
        except Exception as e:
            raise TaskConfigError("Failed to parse schedule.") from e

        try:
            # this will not resolve fully because we are using the unbound attempt methods
            # this is just to validate the attempt methods/functions being used after parsing
            _ = parser.resolve(self._parse_result)
        except Exception as e:
            raise TaskConfigError("Failed to validate schedule.") from e

    def __call__(self) -> ScheduledAgent:
        actuators = [cls() for cls in self._actuator_types]
        attempts = {
            attempt.__name__: attempt
            for _, attempt in self._get_all_attempt_methods(actuators)
        }
        # create schedule from bound methods. these methods are now tied to the list of actuators!
        schedules = schedule_parser.resolve(
            self._parse_result, attempts, self._functions
        )
        return ScheduledAgent(actuators, schedules)

    def _iter_attempt_methods_unbound(self, actuator: Type[Actuator]):
        assert issubclass(actuator, Actuator)
        for fun in actuator.__attemptmethods__:
            yield actuator, fun

    def _iter_attempt_methods_bound(self, actuator: Actuator):
        assert isinstance(actuator, Actuator)
        for fun in actuator.__attemptmethods__:
            yield actuator, MethodType(fun, actuator)  # bind

    def _get_all_attempt_methods(self, actuators: List[Actuator | Type[Actuator]]):
        if len(actuators) == 0:
            return iter([])
        if isinstance(actuators[0], Actuator):
            return itertools.chain(
                *[self._iter_attempt_methods_bound(actu) for actu in actuators]
            )
        elif issubclass(actuators[0], Actuator):
            return itertools.chain(
                *[self._iter_attempt_methods_unbound(actu) for actu in actuators]
            )
        else:
            raise TypeError(f"Invalid type: {type(actuators[0])}")
