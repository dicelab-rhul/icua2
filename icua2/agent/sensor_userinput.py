from typing import Tuple, Type
from star_ray import Event, Sensor
from star_ray.pubsub import Subscribe


class UserInputSensor(Sensor):

    def __init__(self, subscribe_to: Tuple[Type[Event]] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribe_to = subscribe_to if subscribe_to else tuple()

    def __subscribe__(self):
        return [Subscribe(topic=event_type) for event_type in self._subscribe_to]
