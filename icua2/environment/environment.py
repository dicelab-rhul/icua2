from typing import List, Dict, Callable
import asyncio

from icua2.utils._schedule import ScheduledAgent
from star_ray import Environment, Agent, Actuator
from .ambient import MultiTaskAmbient
from ..utils import LOGGER
from .agent_scheduler import AgentScheduler


class MultiTaskEnvironment(Environment):

    def __init__(
        self,
        agents: List[Agent] = None,
        xml: str = None,
        xml_namespaces: Dict[str, str] = None,
        enable_dynamic_loading: bool = False,
        suppress_warnings: bool = False,
        wait=0.05,
    ):
        ambient = MultiTaskAmbient(
            agents=agents,
            xml=xml,
            xml_namespaces=xml_namespaces,
            enable_dynamic_loading=enable_dynamic_loading,
            suppress_warnings=suppress_warnings,
        )
        super().__init__(
            ambient=ambient,
            wait=wait,
            sync=True,
        )
        self._agent_scheduler = None

    def enable_task(self, task_name: str):
        # TODO what if this is remote!
        self._ambient._inner.enable_task(task_name)

    def disable_task(self, task_name: str):
        self._ambient._inner.disable_task(task_name)

    def register_task(
        self,
        name: str,
        path: str,
        agent_actuators: List[Callable[[], Actuator]] = None,
        avatar_actuators: List[Callable[[], Actuator]] = None,
        enable: bool = False,
    ):
        self._ambient._inner.register_task(
            name,
            path,
            agent_actuators=agent_actuators,
            avatar_actuators=avatar_actuators,
            enable=enable,
        )

    def run(self):
        async def _run():
            event_loop = asyncio.get_event_loop()
            await self.__initialise__(event_loop)
            await asyncio.gather(*self.get_schedule())

        asyncio.run(_run())

    async def __initialise__(self, event_loop):
        await self._ambient.__initialise__()
        await self.initialise_agents()
        LOGGER.debug("Environment initialised successfully.")

    def get_schedule(self):
        tasks = []
        for agent in self._ambient.get_agents():
            if isinstance(agent.get_inner(), ScheduledAgent):
                # schedule agents are fully async, they will wait to execute according to their schedule.
                tasks.append(asyncio.create_task(self.run_agent_no_wait(agent)))
            else:
                tasks.append(asyncio.create_task(self.run_agent(agent)))
        return tasks

    async def run_agent_no_wait(self, agent) -> bool:
        # TODO check that the agent is alive...
        while self._ambient.is_alive:  # check that the agent is alive...?
            await agent.__sense__(self._ambient)
            await agent.__cycle__()
            await agent.__execute__(self._ambient)

    async def run_agent(self, agent) -> bool:
        # TODO check that the agent is alive...
        while self._ambient.is_alive:  # check that the agent is alive...?
            await asyncio.sleep(self._wait)
            await agent.__sense__(self._ambient)
            await agent.__cycle__()
            await agent.__execute__(self._ambient)

    # async def __initialise__(self, event_loop):
    #     await self._ambient.__initialise__()
    #     LOGGER.debug("Environment initialised successfully.")

    # def run(self):
    #     async def _run():
    #         event_loop = asyncio.get_event_loop()
    #         await self.__initialise__(event_loop)
    #         self._agent_scheduler = AgentScheduler(
    #             self._ambient, event_loop, wait=self._wait
    #         )
    #         await self._agent_scheduler.run()

    #     asyncio.run(_run())

    # def get_schedule(self):
    #     raise ValueError(
    #         "`get_schedule` is not used in this environment implementation."
    #     )  # this is not used..
