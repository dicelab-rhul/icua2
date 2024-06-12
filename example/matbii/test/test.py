import asyncio

import ray


async def infinite_task(task_name):
    while True:
        await asyncio.sleep(0.1)
        # print(f"{task_name} running...")


@ray.remote
def ray_task(task_name):
    async def _inf():
        while True:
            await asyncio.sleep(0.1)
            # print(task_name)

    asyncio.run(_inf())
    print("exit?")


objref = None


async def main():
    ray.init()

    # Create initial tasks
    # tasks = [asyncio.create_task(infinite_task(f"Task {i}")) for i in range(3)]
    tasks = []

    async def async_ray():
        print("async ray start")
        global objref
        objref = ray_task.remote("remote")
        await objref
        print("async ray done")

    tasks.append(asyncio.create_task(async_ray()))

    # Wait for a certain duration
    await asyncio.sleep(1)
    ray.cancel(objref)

    await asyncio.gather(*tasks)
    ray.shutdown()


asyncio.run(main())
