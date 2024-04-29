# import asyncio
# from typing import List
# from random import uniform, randint
# from types import MethodType
# from pyfuncschedule import ScheduleParser, Schedule
# from star_ray import Actuator

# from ._logging import LOGGER


# def get_attempt_methods(actuator: Actuator):
#     for fun in actuator.__class__.__attemptmethods__:
#         yield MethodType(fun, actuator)


# def loads(actuators: List[Actuator], schedule: str) -> List[Schedule]:
#     parser = ScheduleParser()
#     # these are registered functions by default
#     parser.register_function(uniform)
#     parser.register_function(randint)
#     parser.register_function(min)
#     parser.register_function(max)

#     # register actuator `attempt` methods
#     for actuator in actuators:
#         for fun in get_attempt_methods(actuator):
#             LOGGER.debug(
#                 "Registered attempt in schedule: %s@%s", actuator, fun.__name__
#             )
#             parser.register_action(fun)

#     schedules = parser.parse(schedule)
#     schedules = parser.resolve(schedules)
#     LOGGER.debug(
#         "Successfully loaded schedule:\n    %s",
#         "\n    ".join(str(sch) for sch in schedules),
#     )
#     return schedules


# def load(actuators: List[Actuator], schedule_file: str) -> List[Schedule]:
#     LOGGER.debug("Reading schedule file: `%s`", schedule_file)
#     with open(schedule_file, "r", encoding="UTF-8") as f:
#         schedule_str = f.read()
#     return loads(actuators, schedule_str)
