"""Module containing the `AvatarActuator`, see class documentation for details."""

from star_ray.agent import Actuator, attempt

from icua.event import RenderEvent, UserInputEvent


class AvatarActuator(Actuator):
    """This actuator will forward all user generated events to the environment. Other agents may subscribe to receive these events, otherwise they will simply be logged. It may also be used to produce `RenderEvent`s which should be taken at the START of the UI rendering step performed by the avatar."""

    @attempt
    def render(self, action: RenderEvent):
        """Attempt method that will attempt a `RenderEvent`."""
        return action

    @attempt
    def default(self, action: UserInputEvent):
        """Default attempt method for this actuator, will simply forward any of the received types to the environment. Typically it will recieve all types present in `UserInputEvent` (assuming that the actuator is attached to an `Avatar`.

        Args:
            action (UserInputEvent): user input event.

        Returns:
            Event: the given `action`
        """
        return action
