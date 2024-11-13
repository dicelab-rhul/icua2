"""Task acceptability functionality. The `TaskAcceptabilitySensor` can be extended to track the state of a task when used as part of a `icua.agent.GuidanceAgent`."""

from abc import abstractmethod
from typing import Any
from pydantic import computed_field
from copy import deepcopy
from star_ray.agent import Sensor
from star_ray.event import Event, Observation, ErrorObservation
from star_ray_xml import Select

__all__ = ("TaskAcceptabilityObservation", "TaskAcceptabilitySensor")


class TaskAcceptabilityObservation(Observation):
    """Observation representing the acceptability and activity of a given task.

    The `values` attribute contains the following fields:
    - `task` (str): the name of the task.
    - `is_active` (bool): whether the task is currently active.
    - `is_acceptable` (bool): whether the task is in an acceptable state, this is always False if `is_active` is False.
    """

    @computed_field
    @property
    def task(self) -> str:
        """Getter for the name of the task."""
        return self.values["task"]

    @computed_field
    @property
    def is_active(self) -> str:
        """Whether the task is currently active."""
        return self.values["is_active"]

    @computed_field
    @property
    def is_acceptable(self) -> str:
        """Whether the task is in an acceptable state, this is always False if `is_active` is False."""
        return self.values["is_acceptable"]


class TaskAcceptabilitySensor(Sensor):
    """This `Sensor` can be used by an agent to track the acceptability of a task."""

    def __init__(self, task_name: str, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            task_name (str): task to track.
            args (list[Any]): Additional optional arguments.
            kwargs (dict[str,Any]): Additional optionals keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._task_name = task_name
        self._beliefs = dict()
        self._errors = []

    @abstractmethod
    def is_acceptable(self, task: str = None, **kwargs) -> bool:
        """Checks whether the task(s) tracked by this `Sensor` is in an acceptable state given current beliefs about it.

        Args:
            task (str, optional): task to check (if this `Sensor` is tracking more than one task). Defaults to None, which indicate the main task this `Sensor` is tracking.
            kwargs (Dict[str, Any], optional): any additional arguments
        Returns:
            bool: whether the task is acceptable.
        """

    @abstractmethod
    def is_active(self, task: str = None, **kwargs) -> bool:
        """Checks whether the task(s) tracked by this `Sensor` is active in the environment.

        Args:
            task (str, optional): task to check (if this `Sensor` is tracking more than one task). Defaults to None, which indicate the main task this `Sensor` is tracking.
            kwargs (Dict[str, Any], optional): any additional arguments
        Returns:
            bool: whether the task is active.
        """

    @abstractmethod
    def sense(self) -> list[Select]:
        """Sense actions that are relevant for tracking the acceptability for the given task. This method will be called automatically during the sense cycle of this `Sensor`. The resulting observations are stored internally and used to determine the acceptability of the given task.

        Returns:
            List[Select]: sense actions.
        """

    def sense_element(
        self, element_id: str = None, xpath: str = None, attributes: list[str] = None
    ) -> Select:
        """Factory for a sensor action that will sense an element with a given `id`.

        Args:
            element_id (str, optional): `id` of the element to sense  (if `xpath` is not provided). Defaults to None.
            xpath (str, optional): xpath of the element (if `element_id` is not provided). Defaults to None.
            attributes (list[str], optional): element attributes to sense. Defaults to None.

        Raises:
            ValueError: if both `element_id` and `xpath` are provided.

        Returns:
            Select: the sense action.
        """
        # TODO maybe this could be in a parent class? e.g. an XMLSensor?
        if element_id is None and xpath is None:
            raise ValueError("One of: `element_id` or `xpath` must be specified.")
        elif element_id:
            xpath = f"//*[@id='{element_id}']"
        if attributes is None:
            attributes = []
        if "id" not in attributes:
            attributes.append("id")
        return Select(xpath=xpath, attrs=attributes)

    def iter_observations(self):  # noqa
        yield from self._errors
        self._errors.clear()
        is_active = self.is_active(self.task_name)
        if not is_active:
            yield TaskAcceptabilityObservation(
                values=dict(
                    task=self.task_name, is_active=is_active, is_acceptable=False
                ),
            )
        else:
            yield TaskAcceptabilityObservation(
                values=dict(
                    task=self.task_name,
                    is_active=is_active,
                    is_acceptable=self.is_acceptable(),
                ),
            )

    def __sense__(self) -> list[Event]:  # noqa
        actions = self.sense()
        # sense() must return a list of actions!
        if not isinstance(actions, list | tuple):
            raise TypeError(
                f"`sense()` must return a `list` of events, received: {type(actions)}"
            )
        return actions

    def __transduce__(self, observations: list[Observation]) -> list[Observation]:  # noqa
        # This is called whenever a new observation is sensed by this sensor (either via __query__ or __notify__).
        # The observations are consumed by the sensor to update the current beliefs.
        # New observations will be generated in `iter_observations` based on the beliefs,
        # typically these will indicate if the acceptability of the task has changed.
        # The agent can also access this information directly using the `is_acceptable` method.
        for observation in observations:
            self._on_observation(observation)
        return []

    @property
    def beliefs(self) -> dict[str, Any]:
        """The `Sensor's` current beliefs about the state of the task.

        Returns:
            Dict[str, Any]: beliefs about the state of the task.
        """
        return self._beliefs

    @property
    def task_name(self) -> str:
        """The name of the task that this `Sensor` is tracking.

        Returns:
            _type_: _description_
        """
        return self._task_name

    def _on_observation(self, observation: Observation | ErrorObservation):
        """Method called internally to handle observations."""
        if isinstance(observation, ErrorObservation):
            self.on_error_observation(observation)
        elif isinstance(observation, Observation):
            self.on_observation(observation)
        else:
            raise TypeError(f"Invalid observation type: {type(observation)}")

    def on_error_observation(self, observation: ErrorObservation):
        """Handle observation errors, which may occur if for example, required task elements are missing during sense actions. By default these error observations will be produced by `iter_observations` delegating the error handling to the agent. Override this method if you want custom behaviour for handling errors.

        Args:
            observation (ErrorObservation): error observation.
        """
        self._errors.append(observation)

    def on_observation(self, observation: Observation):
        """Called when a new observation is received by this sensor. By default this sensors beliefs are updated with this new observation, all observation data (in the field `values`) is added to the `belief` map with the element 'id' as the belief key.

        Args:
            observation (Observation): observation to update beliefs with.
        """
        for data in observation.values:
            try:
                self._beliefs[data.pop("id")] = deepcopy(data)
            except KeyError:
                raise KeyError(
                    f"Observation: {observation} doesn't contain the required `id` attribute."
                )
