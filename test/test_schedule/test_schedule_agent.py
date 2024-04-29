import asyncio
import aiostream
import sys
import time
from typing import List

from icua2.utils.schedule import loads
from pyfuncschedule import Schedule
from star_ray.agent import Agent, attempt, Actuator


schedule = """
test1() @ [1]:3
test2() @ [2]:2
"""
start_time = time.time()


class TestActuator(Actuator):

    @attempt
    def test1(self):
        print(f"test1@{time.time() - start_time}")
        return 1

    @attempt
    def test2(self):
        print(f"test2@{time.time() - start_time}")
        return 2

    @attempt
    def test3(self):
        print(f"test3@{time.time() - start_time}")
        return 3


class ScheduleAgent(Agent):

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

    async def __kill__(self):
        await self._iter_context.aclose()


async def main():
    actuators = [TestActuator()]
    sch = loads(actuators, schedule)
    agent = ScheduleAgent(actuators, sch)
    await agent.__initialise__()
    for i in range(1):
        await agent.__cycle__()
    # await agent.__kill__()


# Run the event loop
asyncio.run(main())
