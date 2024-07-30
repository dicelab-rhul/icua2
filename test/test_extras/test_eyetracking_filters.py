"""Test eye tracking filters with a stub eytracker."""

from icua.extras.eyetracking import (
    EyetrackerIOSensor,
    EyetrackerBase,
    EyeMotionEventRaw,
)
from star_ray.event import WindowMoveEvent, WindowResizeEvent, ScreenSizeEvent

from star_ray import Event


class EyetrackerStub(EyetrackerBase):  # noqa
    def get_nowait(self) -> list[Event]:  # noqa
        return [
            EyeMotionEventRaw(position=(float("nan"), float("nan"))),
            EyeMotionEventRaw(position=(-0.1, 0.1)),
        ]

    async def get(self):  # noqa
        return super().get()

    def start(self) -> None:  # noqa
        return super().start()

    def stop(self) -> None:  # noqa
        return super().stop()


sensor = EyetrackerIOSensor(EyetrackerStub())
sensor.on_window_move(WindowMoveEvent(position=(0, 0)))
sensor.on_window_resize(WindowResizeEvent(size=(100, 100)))
sensor.on_screen_size(ScreenSizeEvent(size=(100, 100)))


sensor.__query__(None)
for obs in sensor.iter_observations():
    print(obs)
