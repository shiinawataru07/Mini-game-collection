"""Small deterministic helpers shared by tests."""


class FixedRandom:
    def __init__(self, random_value: float = 0.5) -> None:
        self.random_value = random_value

    def choice(self, values):
        return values[0]

    def random(self) -> float:
        return self.random_value

