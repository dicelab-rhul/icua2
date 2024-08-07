"""Bridge between the Tobii (pro) eyetracking API and the `icua` eyetracking API."""

import time
import traceback
from queue import Queue
from .error import EyetrackingConfigurationError
from .eyetrackerbase import EyetrackerBase
from ...utils import LOGGER
from .event import EyeMotionEventRaw
from star_ray import Event

try:
    import tobii_research as _tr  # noqa

    TOBII_RESEACH_SDK_AVALIABLE = True
except ModuleNotFoundError:
    LOGGER.warning("Failed to locate module: `tobii_research`")
    TOBII_RESEACH_SDK_AVALIABLE = False


# constants used by tobii api for raw gaze events
DEVICE_TIME_STAMP = "device_time_stamp"
SYSTEM_TIME_STAMP = "system_time_stamp"
LEFT_GAZE_POINT_ON_DISPLAY_AREA = "left_gaze_point_on_display_area"
LEFT_GAZE_POINT_IN_USER_COORDINATE_SYSTEM = "left_gaze_point_in_user_coordinate_system"
LEFT_GAZE_POINT_VALIDITY = "left_gaze_point_validity"
LEFT_PUPIL_DIAMETER = "left_pupil_diameter"
LEFT_PUPIL_VALIDITY = "left_pupil_validity"
LEFT_GAZE_ORIGIN_IN_USER_COORDINATE_SYSTEM = (
    "left_gaze_origin_in_user_coordinate_system"
)
LEFT_GAZE_ORIGIN_IN_TRACKBOX_COORDINATE_SYSTEM = (
    "left_gaze_origin_in_trackbox_coordinate_system"
)
LEFT_GAZE_ORIGIN_VALIDITY = "left_gaze_origin_validity"
RIGHT_GAZE_POINT_ON_DISPLAY_AREA = "right_gaze_point_on_display_area"
RIGHT_GAZE_POINT_IN_USER_COORDINATE_SYSTEM = (
    "right_gaze_point_in_user_coordinate_system"
)
RIGHT_GAZE_POINT_VALIDITY = "right_gaze_point_validity"
RIGHT_PUPIL_DIAMETER = "right_pupil_diameter"
RIGHT_PUPIL_VALIDITY = "right_pupil_validity"
RIGHT_GAZE_ORIGIN_IN_USER_COORDINATE_SYSTEM = (
    "right_gaze_origin_in_user_coordinate_system"
)
RIGHT_GAZE_ORIGIN_IN_TRACKBOX_COORDINATE_SYSTEM = (
    "right_gaze_origin_in_trackbox_coordinate_system"
)
RIGHT_GAZE_ORIGIN_VALIDITY = "right_gaze_origin_validity"


class TobiiEyetracker(EyetrackerBase):
    """This class exposes the Tobii (pro) eyetracking API. It may be used by an avatar (or the environment) to get data on a users gaze location."""

    def __init__(
        self,
        uri: str | None = None,
        **kwargs,
    ):
        """Constructor.

        Args:
            uri (str): the unique address of the eyetracker hardware, this can be found in the `Tobii Pro Eyetracker Manager` example: "tet-tcp://172.28.195.1". This software should also be used to calibrate the eyetracker, there is currently no built in calibrating from within the icua system. Defaults to None, in which case the first avaliable eyetracker will be used.
            kwargs (dict[str,Any]): additional optional keyword arguments.

        Raises:
            ModuleNotFoundError: If the required `tobii_research` module could not be found.
        """
        # the module was not found, but someone is trying to create an instance of this class!
        try:
            import tobii_research as _  # noqa
        except ModuleNotFoundError as e:
            raise e

        super().__init__()

        self._buffer = Queue()
        self._uri = uri
        self._eyetracker = None
        self._t0 = None

        if uri is None:
            eyetrackers = _tr.find_all_eyetrackers()
            if eyetrackers:
                self._eyetracker = eyetrackers[0]
            else:
                raise EyetrackingConfigurationError(
                    "No eyetrackers were found, check that the eyetracker is connected and avaliable in the official Tobii Pro Eye Tracker Manager software."
                )
        else:
            try:
                self._eyetracker = _tr.EyeTracker(self._uri)
            except Exception as exception:
                raise EyetrackingConfigurationError(
                    f"Failed to initialise eyetracker at uri: {self._uri}, see cause above. Also check that the eyetracker is connected and avaliable in the official Tobii Pro Eye Tracker Manager software. "
                ) from exception

    def start(self):  # noqa
        try:
            # so we can track the actual times (this will introduce a small error...)
            self._t0 = (_tr.get_system_time_stamp(), time.time())
            self._eyetracker.subscribe_to(
                _tr.EYETRACKER_GAZE_DATA,
                self._internal_callback,
                as_dictionary=True,
            )
        except Exception as exception:
            LOGGER.exception(f"Tobii Eyetracker {self._uri} failed to start.")
            # TODO do we want to stop execution when this happens? maybe give an option to continue?
            raise exception
        LOGGER.info(f"Tobii Eyetracker {self._uri} created successfully.")

    def stop(self):  # noqa
        self._eyetracker.unsubscribe_from(
            _tr.EYETRACKER_GAZE_DATA, self._internal_callback
        )

    def _internal_callback(self, gaze_sample) -> None:
        try:
            dt = (gaze_sample[SYSTEM_TIME_STAMP] - self._t0[0]) / 10e5
            timestamp = self._t0[1] + dt
            point = None
            if (
                gaze_sample[LEFT_GAZE_ORIGIN_VALIDITY]
                and gaze_sample[RIGHT_GAZE_POINT_VALIDITY]
            ):
                left_sample = gaze_sample[LEFT_GAZE_POINT_ON_DISPLAY_AREA]
                right_sample = gaze_sample[RIGHT_GAZE_POINT_ON_DISPLAY_AREA]
                point = (
                    (left_sample[0] + right_sample[0]) / 2,
                    (left_sample[1] + right_sample[1]) / 2,
                )
            elif gaze_sample[LEFT_GAZE_POINT_VALIDITY]:
                point = gaze_sample[LEFT_GAZE_POINT_ON_DISPLAY_AREA]
            elif gaze_sample[RIGHT_GAZE_POINT_VALIDITY]:
                point = gaze_sample[RIGHT_GAZE_POINT_ON_DISPLAY_AREA]
            else:
                # it is useful to know when eyetracking events failed
                point = (float("nan"), float("nan"))
            event = EyeMotionEventRaw(timestamp=timestamp, position=point)
            # this is called from another thread (managed by tobii_research, it needs to happen in a thread safe way)
            self._buffer.put_nowait(event)
            # asyncio.get_event_loop().call_soon_threadsafe(
            #    self._buffer.put_nowait, event
            # )
        except Exception as e:
            traceback.print_exception(e)

    async def get(self) -> list[Event]:  # noqa
        items = []
        items.append(await self._buffer.get())
        while not self._buffer.empty():
            item = self._buffer.get_nowait()
            items.append(item)
        return items

    def get_nowait(self) -> list[Event]:  # noqa
        items = []
        while not self._buffer.empty():
            item = self._buffer.get_nowait()
            items.append(item)
        return items
