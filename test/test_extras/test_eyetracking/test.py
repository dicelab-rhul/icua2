from icua2.extras.eyetracking.tobii import TobiiEyetracker

import time
import asyncio


async def main():
    eyetracker = TobiiEyetracker("tet-tcp://172.28.195.1", sampling_rate=None)
    async for x in eyetracker.start():
        print(x)


if __name__ == "__main__":

    asyncio.run(main())
