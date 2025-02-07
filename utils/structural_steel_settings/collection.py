from typing import Generic, Iterator, List, TypeVar, Union

T = TypeVar("T")


class Collection(Generic[T]):
    def __init__(self):
        self.items: List[T] = []

    def add_item(self, item: T):
        self.items.append(item)

    def remove_item(self, item: T):
        self.items.remove(item)

    def get(self, name: str) -> Union[T, None]:
        for item in self.items:
            if item.name == name:
                return item
        return None

    def clear(self):
        self.items.clear()

    def to_dict(self) -> List[str]:
        return [item.name for item in self.items]

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)
