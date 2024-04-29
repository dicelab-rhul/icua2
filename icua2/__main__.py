from importlib.resources import files

from icua2.guidance import GuidanceAgent
from matbii.environment import MatbiiEnvironment

__package__ = "icua2"
if __name__ == "__main__":
    schedule_file = str(files(__package__).parent / "schedule.sch")
    enabled_tasks = [
        "task_system_monitoring",
        "task_tracking",
        "task_resource_management",
    ]
    env = MatbiiEnvironment(
        agents=[GuidanceAgent()],
        enabled_tasks=enabled_tasks,
        schedule_file=schedule_file,
        wait=0.01,
    )
    env.run()
