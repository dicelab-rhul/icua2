from icua2.agent import agent, attempt, Actuator
from star_ray.plugin.xml import QueryXPath


@agent
class FollowActuator(Actuator):

    @attempt
    def move(self, direction):
        print(direction)
        return QueryXPath(
            xpath="//svg/circle", attributes=dict(x=direction[0], y=direction[1])
        )
