"""Tests the `ScheduledAgent` class."""

from collections.abc import Callable
import asyncio
import inspect
import pyfuncschedule as sch
from star_ray import Actuator, attempt, Event
import time

from icua.utils._schedule import merge_iterators


class Stub(Actuator):
    """Stub actuator."""

    @attempt
    def take1(self):  # noqa
        return Event(source=1)

    @attempt
    def take2(self):  # noqa
        return Event(source=2)

    @attempt
    def take3(self):  # noqa
        return Event(source=3)

    @attempt
    def take4(self):  # noqa
        raise ValueError()


def get_attempts(actuator: Actuator) -> dict[str, Callable]:
    """Get all attempt methods in actuator."""
    methods = inspect.getmembers(actuator, predicate=inspect.ismethod)
    return {m[0]: m[1] for m in filter(lambda m: hasattr(m[1], "is_attempt"), methods)}


SCHEDULE = """
take1() @ [0.1]:5
take2() @ [0.05, [0.1]:5]:1
take3() @ [0.1]:5
take4() @ [2]:1
"""


async def main():
    """Entry point."""
    schedule = sch.parse(SCHEDULE)
    actuator = Stub()
    actions = get_attempts(actuator)
    schedules = sch.resolve(schedule, actions=actions, functions={})
    iters = [iter(s) for s in schedules]
    start_time = time.time()
    async for x in merge_iterators(iters):
        print(type(x), x(), time.time() - start_time)


if __name__ == "__main__":
    asyncio.run(main())
