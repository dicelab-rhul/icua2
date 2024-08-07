"""Test ScheduledAgent class."""

import time
import asyncio
import inspect
from collections.abc import Callable
from star_ray import Actuator, attempt, Event, Agent
import pyfuncschedule as sch
from icua.utils import ScheduledAgent

SCHEDULE = """
take1() @ [0.05]:100
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


class OtherAgent(Agent):
    """Other agent that is slow."""

    def __cycle__(self):  # noqa
        time.sleep(0.1)


if __name__ == "__main__":

    async def main():  # noqa
        schedule = sch.parse(SCHEDULE)
        actuator = Stub()
        actions = get_attempts(actuator)
        schedules = sch.resolve(schedule, actions=actions, functions={})

        async def _run_sch_agent():
            agent = ScheduledAgent([actuator], schedules)
            while not agent._completed:
                await agent.__cycle__()

        async def _run_slow_agent():
            agent = OtherAgent([], [])
            for _ in range(20):
                await asyncio.sleep(0.01)
                agent.__cycle__()

        task_sch = asyncio.create_task(_run_sch_agent())
        task_slow = asyncio.create_task(_run_slow_agent())

        await asyncio.wait([task_sch, task_slow], return_when=asyncio.ALL_COMPLETED)

        import numpy as np

        print("mean dt:", np.mean(dts), "std dt:", np.std(dts))

    asyncio.run(main())
