from typing import List, Dict, Callable
from star_ray import Environment, Agent, Actuator
from .ambient import MultiTaskAmbient


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
        # self._webserver = MatbiiWebServer(ambient, MatbiiAvatar.get_factory())

    def enable_task(self, task_name: str):
        self._ambient._inner.enable_task(task_name)

    def disable_task(self, task_name: str):
        self._ambient._inner.disable_task(task_name)

    def register_task(
        self,
        name: str,
        path: str,
        agent_actuators: List[Callable[[], Actuator]] = None,
        avatar_actuators: List[Callable[[], Actuator]] = None,
    ):
        self._ambient._inner.register_task(
            name,
            path,
            agent_actuators=agent_actuators,
            avatar_actuators=avatar_actuators,
        )

    def get_schedule(self):
        tasks = super().get_schedule()
        return tasks
        # run the web server :) it is running on the main thread here, so we can just run it as a task.
        # there may be more complex setups where it is run remotely... TODO think about how this might be done.
        # return tasks
        # webserver_task = asyncio.create_task(self._webserver.run(port=8888))
        # return [webserver_task, *tasks]

    async def step(self) -> bool:
        self._cycle += 1
        # return False if the simulation should stop? TODO more info might be useful...
        agents = self._ambient.get_agents()
        await self._step(agents)
        return True
