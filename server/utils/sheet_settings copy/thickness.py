class Thickness:
    def __init__(self, name: str):
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: "Thickness"):
        return isinstance(other, Thickness) and self.name == other.name
