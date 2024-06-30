from typing import List, Dict, Callable, Any, Tuple
import asyncio

from icua2.utils._schedule import ScheduledAgent
from star_ray import Environment, Agent, Actuator
from .ambient import MultiTaskAmbient
from ..utils import LOGGER


class MultiTaskEnvironment(Environment):

    def __init__(
        self,
        agents: List[Agent] = None,
        svg: str = None,
        namespaces: Dict[str, str] = None,
        enable_dynamic_loading: bool = False,
        suppress_warnings: bool = False,
        wait: float = 0.05,
        svg_size: Tuple[float, float] = None,
        svg_position: Tuple[float, float] = None,
    ):
        ambient = MultiTaskAmbient(
            agents=agents,
            svg=svg,
            namespaces=namespaces,
            enable_dynamic_loading=enable_dynamic_loading,
            suppress_warnings=suppress_warnings,
            svg_size=svg_size,
            svg_position=svg_position,
        )
        super().__init__(
            ambient=ambient,
            wait=wait,
            sync=True,
        )
        self._agent_scheduler = None

    def enable_task(
        self, task_name: str, context: Dict[str, Any] = None, insert_at: int = 0
    ):
        # TODO what if this is remote!
        self._ambient._inner.enable_task(
            task_name, context=context, insert_at=insert_at
        )

    def disable_task(self, task_name: str):
        self._ambient._inner.disable_task(task_name)

    def rename_task(self, task_name: str, new_name: str):
        self._ambient._inner.rename_task(task_name, new_name)

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
        print("??")

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
