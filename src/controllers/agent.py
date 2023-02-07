class BaseAgent:
    def act(self, observations):
        raise NotImplementedError


class BaselineAgent(BaseAgent):
    def __init__(self):
        self.counter = 0

    def act(self, observations):
        self.counter += 1
        if self.counter % 2 == 0:
            return 2
        else:
            return 3
