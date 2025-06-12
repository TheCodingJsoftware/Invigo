class Material:
    def __init__(self, name: str):
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: "Material"):
        return isinstance(other, Material) and self.name == other.name
