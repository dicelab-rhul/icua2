from star_ray.agent import Actuator, attempt

from icua2.event import *


class DefaultActuator(Actuator):
    """This actuator will forward all user generated events to the environment. Other agents may subscribe to receive these events, otherwise they will simply be logged."""

    @attempt
    def default(self, action: EyeMotionEvent | MouseMotionEvent | MouseButtonEvent | KeyEvent | WindowOpenEvent | WindowCloseEvent | WindowFocusEvent | WindowMoveEvent | WindowResizeEvent):
        """Default attempt method for this actuator, will simply forward any of the received types to the environment.

        Args:
            action (EyeMotionEvent | MouseMotionEvent | MouseButtonEvent | KeyEvent | WindowOpenEvent | WindowCloseEvent | WindowFocusEvent | WindowMoveEvent | WindowResizeEvent): user input event.

        Returns:
            Event: the given `action`
        """
        return action
