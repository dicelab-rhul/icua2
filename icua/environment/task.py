"""TODO."""
# from pydantic import BaseModel
# from abc import ABC, abstractmethod
# from star_ray import Agent, Actuator
# from typing import List, Type, Callable

# from ..utils._schedule import ScheduledAgent

# class _Task(BaseModel, ABC):
#     name: str

#     @abstractmethod
#     def get_agent(self, agent: Agent | None = None):
#         pass

#     @abstractmethod
#     def get_avatar(self, avatar: Agent | None = None):
#         pass


# class _ScheduledTask(_Task):

#     agent_actuators: List[Type[Actuator]]
#     avatar_actuators: List[Type[Actuator]]

#     def get_agent(self, agent: Agent | Type[Agent] = None):
#         if agent is None:

#         return _ScheduledTask._initialise_agent(agent, self.agent_actuators)

#     def get_avatar(self, avatar: Agent | Type[Agent] | Callable[[], Agent]):
#         return _ScheduledTask._initialise_agent(avatar, self.avatar_actuators)

#     @staticmethod
#     def _initialise_agent(
#         agent: Agent | Type[Agent] | Callable[[], Agent],
#         actuators: List[Type[Actuator]],
#     ):
#         if isinstance(agent, Agent):
#             for actuator in actuators:
#                 agent.add_component(actuator())
#             return agent
#         else:  # presume this is a type (or factory method)
#             return agent(sensors=[], actuators=[actuator() for actuator in actuators])


# class _TaskDynamicLoad(_Task):
#     path: str
