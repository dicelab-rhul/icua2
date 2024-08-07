"""Test ScheduledAgent class."""

import time
import asyncio
import inspect
from collections.abc import Callable
from star_ray import Actuator, attempt, Event
import pyfuncschedule as sch
from icua.utils import ScheduledAgentAsync

SCHEDULE = """
take1() @ [0.1]:5
take2() @ [0.05, [0.1]:5]:1
take3() @ [0.1]:5
"""

SCHEDULE2 = """
take1() @ [0.1]:20
"""

start_time = time.time()
dts = []


class Stub(Actuator):
    """Stub actuator."""

    @attempt
    def take1(self):  # noqa
        global start_time
        global dts
        t = time.time()
        print(t - start_time, "take1")
        dts.append(t - start_time)
        start_time = t
        return Event(source=1)

    @attempt
    def take2(self):  # noqa
        print(time.time() - start_time, "take2")
        return Event(source=2)

    @attempt
    def take3(self):  # noqa
        print(time.time() - start_time, "take3")
        return Event(source=3)

    @attempt
    def take4(self):  # noqa
        raise ValueError()


def get_attempts(actuator: Actuator) -> dict[str, Callable]:
    """Get all attempt methods in actuator."""
    methods = inspect.getmembers(actuator, predicate=inspect.ismethod)
    return {m[0]: m[1] for m in filter(lambda m: hasattr(m[1], "is_attempt"), methods)}


if __name__ == "__main__":

    async def main():  # noqa
        schedule = sch.parse(SCHEDULE2)
        actuator = Stub()
        actions = get_attempts(actuator)
        schedules = sch.resolve(schedule, actions=actions, functions={})

        agent = ScheduledAgentAsync([actuator], schedules)
        while not agent._completed:
            await agent.__cycle__()
        import numpy as np

        print("mean dt:", np.mean(dts), "std dt:", np.std(dts))

    asyncio.run(main())
