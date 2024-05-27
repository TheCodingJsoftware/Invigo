from typing import Dict, Generic, Iterator, List, Tuple, TypeVar, Union

T = TypeVar("T")


class Collection(Generic[T]):
    def __init__(self):
        self.items: List[T] = []

    def add_item(self, item: T):
        self.items.append(item)

    def remove_item(self, item: T):
        self.items.remove(item)

    def get(self, name: str) -> T:
        for item in self.items:
            if item.name == name:
                return item

    def clear(self):
        self.items.clear()

    def to_dict(self) -> List[str]:
        return [item.name for item in self.items]

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)
