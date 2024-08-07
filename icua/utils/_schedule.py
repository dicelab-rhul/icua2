"""Defines the `ScheduledAgent` class. Agents of this type work with `pyfuncschedule` to periodically execute actions (according to the schedule)."""

import asyncio
import itertools
import inspect

from typing import Generic, TypeVar

from collections.abc import Callable, Iterator, AsyncGenerator
from star_ray import Actuator
import bisect
import time

from star_ray import Agent
from star_ray.environment import State
from star_ray.event import ErrorObservation
from pyfuncschedule import parser as schedule_parser, Schedule, ScheduleParser
from ._logging import LOGGER
from ._error import TaskConfigurationError


class ScheduledAgent(Agent):
    """The actions of this agent are determined by a fixed schedule that is provided upon creation. The schedule is a collection of `attempts` that are part of the given actuators."""

    def __init__(self, actuators: list[Actuator], schedules: list[Schedule]):
        super().__init__([], actuators)
        self._schedules = [iter(sch) for sch in schedules]
        self._next_items = []
        t = time.time()
        # Load the first item from each schedule iterator
        for it in self._schedules:
            try:
                (dt, value) = next(it)
                bisect.insort(
                    self._next_items, ((t + dt, value), it), key=lambda x: x[0][0]
                )
            except StopIteration:
                continue  # Skip if iterator is initially empty

    @property
    def _completed(self):
        return len(self._next_items) == 0

    def __cycle__(self):
        # print(self._next_items)
        # check if there were any errors from actuators
        for actuator in self.actuators:
            for obs in actuator.iter_observations():
                if isinstance(obs, ErrorObservation):
                    raise obs.exception()

        if self._completed:
            LOGGER.warning(
                f"{self} `__cycle__` was called after all schedules have completed."
            )

        while not self._completed:
            # get the earliest item
            (et, attempt), it = self._next_items[0]
            t = time.time()
            nt = et - t
            if nt <= 0:
                # execute immediately and continue to next soonest item
                self._next_items = self._next_items[1:]
                try:
                    (dt, value) = next(it)
                    # nt will compensate for any overshooting
                    bisect.insort(
                        self._next_items,
                        ((t + dt + nt, value), it),
                        key=lambda x: x[0][0],
                    )
                except StopIteration:
                    pass  # no more values, the schedule is complete, try next schedule
                attempt()  # attempt the action
            else:
                break  # no more events scheduled for this cycle


class ScheduledAgentAsync(Agent):
    """The actions of this agent are determined by a fixed schedule that is provided upon creation. The schedule is a collection of `attempts` that are part of the given actuators."""

    def __init__(self, actuators: list[Actuator], schedules: list[Schedule]):
        super().__init__([], actuators)
        self._schedules = [iter(sch) for sch in schedules]
        self._schedules_iter = merge_iterators(self._schedules)
        self._completed = False

    async def __sense__(self, state, *args, **kwargs):
        return super().__sense__(state, *args, **kwargs)

    async def __execute__(self, state, *args, **kwargs):
        return super().__execute__(state, *args, **kwargs)

    async def __terminate__(self):
        self._completed = True
        await self._schedules_iter.aclose()

    async def __initialise__(self, state: State):
        return super().__initialise__(state)

    async def __cycle__(self):
        # check if there were any errors from actuators
        for actuator in self.actuators:
            for obs in actuator.iter_observations():
                if isinstance(obs, ErrorObservation):
                    raise obs.exception()

        if self._completed:
            LOGGER.warning(
                f"{self} `__cycle__` was called after all schedules have completed."
            )
            return  # TODO the agent should take an action which terminates itself!
        try:
            # this will await the next action from the collection of schedules
            attempt = await self._schedules_iter.__anext__()
            attempt()  # attempt the action
            # repeatedly try and get elements if they are yielded in a very short window,
            # if a timeout occurs then yield control back to the main event loop
            # don't try take too many elements, otherwise this may hog the event loop
            # for _ in range(1000):
            #     try:
            #         print("__")
            #         attempt = await asyncio.wait_for(
            #             self._schedules_iter.__anext__(), 0
            #         )
            #         attempt()  # attempt the action
            #     except asyncio.TimeoutError:
            #         print("?")
            #         break  # no more items were immediately avaliable
        except StopAsyncIteration:
            self._completed = True
            LOGGER.debug(f"{self} has completed all its scheduled events.")
        except asyncio.CancelledError:
            self._completed = True
            LOGGER.debug(f"{self} was cancelled.")


class ScheduledAgentFactory:
    def __init__(
        self,
        schedule_source: str,
        actuator_types: list[type[Actuator]],
        funcs: list[Callable],
    ):
        super().__init__()
        self._source = schedule_source
        self._actuator_types = list(set(actuator_types))
        self._functions: dict[str, Callable] = {fun.__name__: fun for fun in funcs}
        self._parse_result: list[Schedule] = None
        self.parse_schedule()

    def parse_schedule(
        self,
    ):
        parser = ScheduleParser()
        for name, fun in self._functions.items():
            parser.register_function(fun, name=name)
            LOGGER.debug(f"registered schedule function: {name}")

        self._attempts = dict()
        for cls, action in self._get_all_attempt_methods(self._actuator_types):
            parser.register_action(action)
            LOGGER.debug(
                f"registered schedule attempt: {cls.__name__}@{action.__name__}"
            )
        try:
            self._parse_result = parser.parse(self._source)
        except Exception as e:
            raise TaskConfigurationError("Failed to parse schedule.") from e

        try:
            # this will not resolve fully because we are using the unbound attempt methods
            # this is just to validate the attempt methods/functions being used after parsing
            _ = parser.resolve(self._parse_result)
        except Exception as e:
            raise TaskConfigurationError("Failed to validate schedule.") from e

    def __call__(self) -> ScheduledAgent:
        actuators = [cls() for cls in self._actuator_types]
        attempts = {
            attempt.__name__: attempt
            for _, attempt in self._get_all_attempt_methods(actuators)
        }
        # create schedule from bound methods, these methods are now tied to the actuators!
        schedules = schedule_parser.resolve(
            self._parse_result, attempts, self._functions
        )
        return ScheduledAgent(actuators, schedules)

    def _iter_attempt_methods_unbound(self, actuator: type[Actuator]):
        assert issubclass(actuator, Actuator)
        methods = inspect.getmembers(actuator, predicate=inspect.isfunction)
        methods = [m[1] for m in filter(lambda m: hasattr(m[1], "is_attempt"), methods)]
        for fun in methods:
            yield actuator, fun

    def _iter_attempt_methods_bound(self, actuator: Actuator):
        assert isinstance(actuator, Actuator)
        methods = inspect.getmembers(actuator, predicate=inspect.ismethod)
        methods = [m[1] for m in filter(lambda m: hasattr(m[1], "is_attempt"), methods)]
        for fun in methods:
            yield actuator, fun

    def _get_all_attempt_methods(self, actuators: list[Actuator | type[Actuator]]):
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


V = TypeVar("V")


async def merge_iterators(
    iterators: list[Iterator[tuple[float, Generic[V]]]],
) -> AsyncGenerator[V]:
    """Merge iterators to create an async iterator that waits for a given time. Each iterator should yield (dt, value). The resulting async iterator will wait (approximately) dt time before yielding the iterator value.

    Args:
        iterators (list[Iterator[tuple[float, V]]]): iterators to merge

    Yields:
        V: values yielded by inner iterators
    """
    # Initialize a list to keep track of the next items from each iterator
    next_items = []

    t = time.time()  # start time
    # Load the first item from each iterator and insert it into the sorted list
    for it in iterators:
        try:
            (dt, value) = next(it)
            bisect.insort(next_items, ((t + dt, value), it), key=lambda x: x[0][0])
        except StopIteration:
            continue  # Skip if iterator is initially empty

    # Process items until all iterators are exhausted
    while next_items:
        # get the earliest item
        (et, value), it = next_items[0]
        t = time.time()
        nt = et - t
        if nt <= 0:
            # execute immediately and continue to next soonest item
            next_items = next_items[1:]
            try:
                (dt, next_value) = next(it)
                # nt will compensate for any overshooting
                bisect.insort(
                    next_items, ((t + dt + nt, next_value), it), key=lambda x: x[0][0]
                )
            except StopIteration:
                pass  # no more values to add the iterator is complete
            yield value
            # allow other tasks to run if iterator dts are too fast...
            await asyncio.sleep(0)
        else:
            # wait for some time
            wait = max(nt / 4, 0.001)
            await asyncio.sleep(wait)
