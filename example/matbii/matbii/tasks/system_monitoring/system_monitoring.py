import random
import re
from typing import Any, ClassVar
from functools import partial
from pydantic import Field, validator

from star_ray_pygame.event import (
    MouseButtonEvent,
)

from icua2.agent import Action, agent_actuator, attempt, Actuator
from star_ray_xml import (
    XMLState,
    Template,
    update,
    select,
)

# these are constants that reflect the task svg
VALID_LIGHT_IDS = [1, 2]
VALID_SLIDER_IDS = [1, 2, 3, 4]


class AvatarSystemMonitoringActuator(Actuator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._get_light_targets = partial(
            AvatarSystemMonitoringActuator.get_click_targets, r"light-(\d+)-button"
        )
        self._get_slider_targets = partial(
            AvatarSystemMonitoringActuator.get_click_targets, r"slider-(\d+)-button"
        )

    @attempt(route_events=[MouseButtonEvent])
    def attempt_mouse_event(self, user_action: MouseButtonEvent):
        assert isinstance(user_action, MouseButtonEvent)
        # always include the user action as it needs to be logged
        actions = [user_action]
        if (
            user_action.status == MouseButtonEvent.DOWN
            and user_action.button == MouseButtonEvent.BUTTON_LEFT
        ):
            actions.extend(self._get_light_actions(user_action))
            actions.extend(self._get_slider_actions(user_action))
        return actions

    def _get_light_actions(self, user_action):
        targets = [int(x) for x in self._get_light_targets(user_action.target)]
        return [ToggleLightAction(target=target) for target in targets]

    def _get_slider_actions(self, user_action):
        targets = [int(x) for x in self._get_slider_targets(user_action.target)]
        return [ResetSliderAction(target=target) for target in targets]

    @staticmethod
    def get_click_targets(pattern, targets):
        def _get():
            for target in targets:
                match = re.match(pattern, target)
                if match:
                    target = match.group(1)
                    yield target

        return list(_get())


@agent_actuator
class SystemMonitoringActuator(Actuator):

    @attempt
    def on_light(self, target: int):
        return SetLightAction(target=target, state=SetLightAction.ON)

    @attempt
    def off_light(self, target: int):
        return SetLightAction(target=target, state=SetLightAction.OFF)

    @attempt
    def toggle_light(self, target: int):
        return ToggleLightAction(target=target)

    @attempt
    def perturb_slider(self, target: int):
        state = 2 * random.randint(0, 1) - 1  # randomly perturb +/- 1
        return SetSliderAction(target=target, state=state, relative=True)


def ToggleSliderAction(target: int) -> "SetSliderAction":
    state = random.randint(0, 1) * 2 - 1
    return SetSliderAction(target=target, state=state, relative=True)


def ResetSliderAction(target: int) -> "SetSliderAction":
    return SetSliderAction(target=target, state=None, relative=False)


class SetSliderAction(Action):

    target: int  # slider to target
    state: (
        int | None
    )  # state to set, or offset from current state, or None if should reset the state.
    relative: bool = Field(
        default_factory=lambda: False
    )  # is `state` relative to the current state?

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if not value in VALID_SLIDER_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    @staticmethod
    def acceptable_state(increments):
        return increments // 2 + 1

    def execute(self, xml_state: XMLState) -> Any:
        # get min and max values for the number of increments
        inc_target = f"slider-{self.target}-incs"
        but_target = f"slider-{self.target}-button"
        response = xml_state.select(
            select(
                xpath=f"//*[@id='{inc_target}']/svg:line",
                attrs=["y1", "data-state"],
            )
        )
        states = {x["data-state"]: x["y1"] for x in response}
        inc_size = states[2] - states[1]  # TODO check that these are all the same?
        min_state, max_state = (min(states.keys()), max(states.keys()) - 1)
        state = self.state
        if state is None:
            self.relative = False
            state = SetSliderAction.acceptable_state(max_state)

        # we select the parent of the button node because it contains the state and position to update
        xpath_parent = f"//*[@id='{but_target}']/parent::node()"
        if self.relative:
            # update the state relative to the current state
            response = xml_state.select(
                select(
                    xpath=xpath_parent,
                    attrs=["data-state"],
                )
            )
            assert len(response) == 1
            state = response[0]["data-state"] + self.state

        # new state should not overflow
        state = min(max(min_state, state), max_state)
        new_y = states[state] - inc_size
        return xml_state.update(
            update(
                xpath=xpath_parent,
                attrs={"data-state": state, "y": new_y},
            )
        )


class SetLightAction(Action):
    target: int
    state: int

    OFF: ClassVar[int] = 0
    ON: ClassVar[int] = 1

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if not value in VALID_LIGHT_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    @validator("state", pre=True, always=True)
    @classmethod
    def _validate_state(cls, value: int | str):
        if isinstance(value, str):
            value = SetLightAction.coerce_light_state(value)
        if not value in (SetLightAction.OFF, SetLightAction.ON):
            raise ValueError(
                f"Invalid state `{value}` must be one of {[SetLightAction.OFF, SetLightAction.ON]}"
            )
        return value

    @staticmethod
    def coerce_light_state(value: str | int):
        if isinstance(value, int):
            return value
        if value == "on":
            return SetLightAction.ON
        elif value == "off":
            return SetLightAction.OFF
        else:
            raise ValueError(f"Invalid state `{value}` must be one of ['on', 'off']")

    def execute(self, xml_state: XMLState):
        xml_state.update(
            update(
                xpath=f"//*[@id='light-{self.target}-button']",
                attrs={
                    "data-state": "%s" % self.state,
                    "fill": Template("{data-colors}[{state}]", state=self.state),
                },
            )
        )


class ToggleLightAction(Action):
    target: int

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if not value in VALID_LIGHT_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    def execute(self, xml_state: XMLState):
        xml_state.update(
            update(
                xpath=f"//*[@id='light-{self.target}-button']",
                attrs={
                    "data-state": Template("1-{data-state}"),
                    # GOTCHA! data-state will be updated first (from above) and used to update fill! the order matters here.
                    "fill": Template("{data-colors}[{data-state}]"),
                },
            )
        )
