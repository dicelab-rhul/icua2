import asyncio
from typing import Any, List, Dict
from star_ray.agent.wrapper_agent import _Agent
from icua2.utils._schedule import ScheduledAgent
from ..utils import LOGGER

KILL_TIMEOUT = 1


class AgentScheduler:

    def __init__(self, ambient, event_loop, wait: float = 0.05):
        super().__init__()
        self._ambient = ambient
        self._event_loop = event_loop
        self._wait = wait  # how long to wait at each loop of an agent

        # set when we want to kill an agent (cancel its running loop)
        self._kill_flag = asyncio.Event()
        # stop this scheduler, TODO this has the side effect of killing all of the agents that were added to it
        self._stop_flag = asyncio.Event()
        # when the kill flag is set, these agents will be killed
        self._kill_agents = []
        self._coroutines = {}

    async def add_agent(self, agent: _Agent):
        # TODO rather than basing this on ScheduledAgent type, we want a generic mechanism to decide
        # what kind of schedule to use for each agent
        # TODO we need to handle the case where the agent is a ray actor...?
        if isinstance(agent.get_inner(), ScheduledAgent):
            # scheduled agents are fully async, they wait to execute according to their schedule.
            # scheudled are never remote, they run on the main thread (this just easier to manage and they are not expensive)
            coroutine = asyncio.create_task(
                self.run_agent_no_wait(agent), name=agent.id
            )
        else:
            coroutine = asyncio.create_task(self.run_agent(agent), name=agent.id)
        self._coroutines[agent.id] = coroutine
        LOGGER.debug("Task created for agent: %s", agent.id)

    async def run(self):
        for agent in self._ambient.get_agents():
            await self.add_agent(agent)

        while not self._stop_flag.is_set():
            if not self._ambient.is_alive:
                # the ambient died, clean up by cancelling all running agents
                LOGGER.debug("Ambient died, cleaning up all agent running loops.")
                self._stop_flag.set()

            kill_coroutine = asyncio.create_task(self._kill_flag.wait())
            done, pending = await asyncio.wait(
                [*self._coroutines.values(), kill_coroutine],
                return_when=asyncio.FIRST_COMPLETED,
            )
            if kill_coroutine in done:
                self._cancel_agent_coroutines()
                done.remove(kill_coroutine)

            # these agents finished
            for agent_coroutine in done:
                exception = agent_coroutine.exception()
                if exception is not None:
                    # TODO default behaviour is to raise the exception?
                    raise exception
                LOGGER.debug("Agent: %s completed", agent_coroutine.get_name())

            # kill all agents and handling any exceptions
            _done, _pending = await asyncio.wait(kill_tasks, timeout=KILL_TIMEOUT)
            if _pending:
                LOGGER.error(
                    "Agents: %s took too long to die, check `__terminate__`for hangs.",
                    [t.getname() for t in pending],
                )
            for t in _done + pending:
                # TODO default behaviour is to raise the exception...
                exception = t.exception()
                if exception:
                    raise exception

        # when we exit, kill / stop all remaining agents
        # self.kill_all()
        # pending = self._kill_agent_coroutines(pending)
        # assert len(pending) == 0  # sanity check, all agents should have been killed...
        # LOGGER.debug("%s stopped successfully.", AgentScheduler.__name__)

    async def _cancel_agent_coroutines(self):
        # the kill coroutine completed, this means that there are agents to kill.. kill them here!
        assert self._kill_flag.is_set()  # sanity check
        assert len(self._kill_agents) > 0  # sanity check, no agents to kill?
        for coroutine in self._kill_agents:
            # this cancels the agents coroutine, the agent should complete, __terminate__ will be called in the next cycle
            coroutine.cancel()
        self._kill_agents.clear()
        self._kill_flag.clear()

    async def stop(self):
        self.kill_all()
        self._stop_flag.set()

    def kill_agent(self, agent_id: Any):
        agent_coroutine = self._coroutines[agent_id]
        self._kill_agents.append(agent_coroutine)
        self._kill_flag.set()

    def kill_all(self):
        for agent_id in list(self._coroutines.keys()):
            agent_coroutine = self._coroutines[agent_id]
            self._kill_agents.append(agent_coroutine)
        self._kill_flag.set()

    async def run_agent_no_wait(self, agent: _Agent):
        try:
            await agent.__initialise__(self._ambient)
            while agent.is_alive:  # check that the agent is alive...?
                await agent.__sense__(self._ambient)
                await agent.__cycle__()
                await agent.__execute__(self._ambient)
        except asyncio.CancelledError:
            LOGGER.debug("Agent: %s running loop was cancelled.", agent.id)

    async def run_agent(self, agent: _Agent):
        try:
            await agent.__initialise__(self._ambient)
            while agent.is_alive:  # check that the agent is alive...?
                await asyncio.sleep(self._wait)
                # t = time.time()
                await agent.__sense__(self._ambient)
                await agent.__cycle__()
                await agent.__execute__(self._ambient)
                # print(agent.get_id(), time.time() - t)
        except asyncio.CancelledError:
            LOGGER.debug("Agent: %s running loop was cancelled.", agent.id)
