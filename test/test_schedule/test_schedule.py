import asyncio
import time
from icua2.utils.schedule import loads
from star_ray.agent import attempt, Actuator


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


sch = loads([TestActuator()], schedule)

# Run the event loop
asyncio.run(sch.run())
