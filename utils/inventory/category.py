class Category:
    def __init__(self, name: str):
        self.name = name

    def rename(self, new_name: str):
        self.name = new_name

    def __eq__(self, other):
        return isinstance(other, Category) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"Category(name={self.name!r})"
