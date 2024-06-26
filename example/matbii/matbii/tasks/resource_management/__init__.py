from cerberus import rules_set_registry
from .resource_management import (
    ResourceManagementActuator,
    AvatarResourceManagementActuator,
    SetPumpAction,
)

__all__ = ("ResourceManagementActuator", "AvatarResourceManagementActuator")

rules_set_registry.add(
    "pump_state",
    {
        "type": "integer",
        "allowed": [0, 1, 2],
        "default": "off",
        "coerce": SetPumpAction.coerce_pump_state,
    },
)
