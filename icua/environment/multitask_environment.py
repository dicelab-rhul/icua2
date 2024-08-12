"""Module defining the `MultiTaskEnvironment`, see class documentation for details."""

import asyncio
from typing import Any
from collections.abc import Callable

from star_ray import Environment, Agent, Actuator
from .multitask_ambient import MultiTaskAmbient

from ..utils import LOGGER


class MultiTaskEnvironment(Environment):
    """Environment implementation that supports "tasks". A task is a modular part of the environment which the user typically interacts with via their `Avatar`. Tasks will typially have an associated agent that updates/manages the tasks state. The users avatar should also provide some means to interact with tasks. When a new task is added, this may mean the avatar gains a new actuator and will often mean that a new agent is added to the environment.

    TODO a thorough explaination of what tasks are and how to define/use them!

    See:
        `MultiTaskAmbient`
    """

    def __init__(
        self,
        avatar: Agent,
        agents: list[Agent] = None,
        wait: float = 0.01,
        svg_size: tuple[float, float] = None,
        svg_position: tuple[float, float] = None,
        logging_path: str = None,
        terminate_after: float = -1,
        **kwargs: dict[str, Any],
    ):
        """Constructor.

        Args:
            avatar (Agent, optional): The users avatar. Defaults to None.
            agents (list[Agent], optional): list of initial agents. Defaults to None.
            wait (float, optional): time to wait between simulation cycles. Defaults to 0.01.
            svg_size (tuple[float, float], optional): size of the root SVG element. Defaults to None (see `MultiTaskAmbient` for details).
            svg_position (tuple[float, float], optional): position of the root SVG element. Defaults to None (see `MultiTaskAmbient` for details).
            logging_path (str, optional): path that events will be logged to. Defaults to None (see `MultiTaskAmbient` for details).
            terminate_after (float, optional): time after which to terminate the simulatio. Defaults to -1 (never terminate).
            kwargs (dict[str, Any]): Additional optional keyword arguments, see `MultiTaskAmbient` for options.
        """
        ambient = MultiTaskAmbient(
            avatar=avatar,
            agents=agents,
            logging_path=logging_path,
            svg_size=svg_size,
            svg_position=svg_position,
            **kwargs,
        )
        super().__init__(
            ambient=ambient,
            wait=wait,
            sync=True,
        )
        # time until termination
        self._terminate_after = terminate_after

    @property
    def ambient(self) -> MultiTaskAmbient:
        """Getter for the inner ambient, which is always a `MultiTaskAmbient`. IMPORTANT NOTE: remote ambients are not currently supported.

        Returns:
            MultiTaskAmbient: the ambient.
        """
        ambient = self._ambient._inner
        # TODO remote ambient currently not supported - this would be easy to do... (just need relevant methods exposed)
        assert isinstance(ambient, MultiTaskAmbient)
        return ambient

    def enable_task(
        self, task_name: str, context: dict[str, Any] = None, insert_at: int = -1
    ):
        """Manually enable a task. Tasks may otherwise be enabled via an `EnableTask` action.

        Args:
            task_name (str): name of the task to enable.
            context (dict[str,Any]): context to use when enabling the task
            insert_at (int): at what position in the SVG tree to insert the task element.
        """
        self.ambient.enable_task(task_name, context=context, insert_at=insert_at)

    def disable_task(self, task_name: str):
        """Manually disable a task. Tasks may otherwise be disabled via an `EnableTask` action.

        Args:
            task_name (str): name of the task to disable.
        """
        self.ambient.disable_task(task_name)

    def rename_task(self, task_name: str, new_name: str) -> None:
        """Rename a task. If the task is enabled this will alter the `id` attribute of the task element (TODO).

        Args:
            task_name (str): current name of the task.
            new_name (str): new name of the task.
        """
        return self.ambient.rename_task(task_name, new_name)

    def add_task(
        self,
        name: str,
        path: str,
        agent_actuators: list[Callable[[], Actuator]] = None,
        avatar_actuators: list[Callable[[], Actuator]] = None,
        enable: bool = False,
    ):
        """Add a new task, this will load all required files and prepare the task but will not start the task (unless `enable` is True). To start the task use `enable_task` or have an agent take the `EnableTask` action.

        Args:
            name (str): the unique name of the task.
            path (str | list[str]): path(s) to task files.
            agent_actuators (list[Callable[[], Actuator]] | None, optional): actuators with which to create agents from a schedule file, see `MultiTaskEnvironment` documentation for details. Defaults to None.
            avatar_actuators (list[Callable[[], Actuator]] | None, optional): actuators that will be added to the avatar upon enabling the task, see `MultiTaskEnvironment` documentation for details. Defaults to None.
            enable (bool, optional): whether to immediately enable the task. Defaults to False.
        """
        # attempt to log the files that will be used in the task
        self.ambient.add_task(
            name,
            path,
            agent_actuators=agent_actuators,
            avatar_actuators=avatar_actuators,
            enable=enable,
        )

    async def __initialise__(self, event_loop):  # noqa
        await self._ambient.__initialise__()

    def get_schedule(self) -> list[asyncio.Task]:  # noqa
        tasks = super().get_schedule()
        # whether to terminate after a given period of time
        if self._terminate_after > 0:

            async def _terminate_after(env: MultiTaskEnvironment):
                try:
                    await asyncio.sleep(env._terminate_after)
                    # TODO perhaps this should be an event that is logged?
                    LOGGER.debug(
                        f"Closing simulation: time limit ({env._terminate_after}s) reached"
                    )
                    await env.ambient.__terminate__()
                except asyncio.CancelledError:
                    pass
                except asyncio.TimeoutError:
                    pass

            tasks.append(asyncio.create_task(_terminate_after(self)))
        return tasks

    # def run(self):  # noqa
    #     async def _cancel_pending_tasks(pending_tasks, timeout=0.5):
    #         """Await pending tasks with a timeout to avoid hanging."""
    #         for pending_task in pending_tasks:
    #             pending_task.cancel()
    #         for pending_task in pending_tasks:
    #             try:
    #                 await asyncio.wait_for(pending_task, timeout=timeout)
    #             except asyncio.CancelledError:
    #                 pass  # print(f"Pending task {pending_task} was cancelled")
    #             except asyncio.TimeoutError:
    #                 LOGGER.warning(
    #                     f"Pending task {pending_task} did not finish within timeout"
    #                 )
    #                 pass

    #     async def _run():
    #         """Run the simulation. This is a custom implementation of run which may be changed in favour of proper scheduling in future versions (if `star_ray` implements support for this)."""
    #         event_loop = asyncio.get_event_loop()
    #         await self.__initialise__(event_loop)
    #         tasks = self.get_schedule()
    #         # The default behaviour here is to exit the program if there is an exception,
    #         # this is because we dont want any silent failures during an experiment as it may invalidate any experimental results.
    #         # if this is not desired behaviour, you should override this method and continue execution after e.g. logging the exception.
    #         done, pending = await asyncio.wait(
    #             tasks, return_when=asyncio.FIRST_EXCEPTION
    #         )
    #         await _cancel_pending_tasks(pending)
    #         for task in done:
    #             e = task.exception()
    #             if e:
    #                 raise e

    #     asyncio.run(_run())

    # def get_schedule(self):  # noqa
    #     tasks = []
    #     for agent in self._ambient.get_agents():
    #         if isinstance(agent.get_inner(), ScheduledAgent):
    #             # schedule agents are fully async, they will wait to execute according to their schedule.
    #             tasks.append(asyncio.create_task(self._run_agent_no_wait(agent)))
    #         else:
    #             tasks.append(asyncio.create_task(self._run_agent(agent)))
    #     return tasks

    # async def _run_agent_no_wait(self, agent) -> None:
    #     """Runs an agent without waiting. This should only be used for agents that have async cycle methods to prevent event loop hogging."""
    #     # TODO check that the agent is alive...
    #     try:
    #         while self._ambient.is_alive:  # check that the agent is alive...?
    #             await agent.__sense__(self._ambient)
    #             await agent.__cycle__()
    #             await agent.__execute__(self._ambient)
    #     except asyncio.CancelledError:
    #         pass
    #     except Exception as e:
    #         raise e  # re-raise

    # async def _run_agent(self, agent) -> None:
    #     """Run an agent in the usual way waiting for a short time before executing each cycle."""
    #     try:
    #         # TODO check that the agent is alive...
    #         while self._ambient.is_alive:  # check that the agent is alive...?
    #             await asyncio.sleep(self._wait / self._ambient.get_agent_count())
    #             await agent.__sense__(self._ambient)
    #             await agent.__cycle__()
    #             await agent.__execute__(self._ambient)
    #     except asyncio.CancelledError:
    #         pass
    #     except Exception as e:
    #         raise e  # re-raise
