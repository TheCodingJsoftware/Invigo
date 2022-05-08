from json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class Geometry:
    """
    For getting the windows geometry
    """

    def __init__(self):
        self.__x: int = self.get_value("x")
        self.__y: int = self.get_value("y")
        self.__width: int = self.get_value("width")
        self.__height: int = self.get_value("height")

    def get_value(self, value: str) -> int:
        return settings_file.get_value(item_name="geometry")[value]

    def x(self) -> int:
        return self.__x

    def y(self) -> int:
        return self.__y

    def width(self) -> int:
        return self.__width

    def height(self) -> int:
        return self.__height
