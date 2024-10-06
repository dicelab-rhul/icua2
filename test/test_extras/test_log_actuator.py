"""Test LogActuator class."""

from icua.extras.logging import LogActuator

if __name__ == "__main__":
    actuator = LogActuator("./test.log")
    actuator.log(dict(a=1, b=2, c=3, d=4))
    actuator.__query__(None)
