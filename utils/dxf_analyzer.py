import trimesh
from trimesh.path import Path2D


class DxfAnalyzer:
    PIERCING_TIME = 2.73157894737  # seconds per piercing point
    CUT_TIME_PER_INCH = 2.87897096597  # seconds per inch of cutting length

    def __init__(self, dxf_path: str):
        self.dxf_path = dxf_path
        self.shape = trimesh.load(dxf_path, force="2D")

        if not isinstance(self.shape, Path2D):
            raise ValueError("DXF did not load as a 2D shape")

    def get_cutting_length(self) -> float:
        return sum(entity.length(self.shape.vertices) for entity in self.shape.entities)

    def get_cutting_area(self) -> float:
        return self.shape.area

    def get_units(self) -> str:
        return self.shape.units

    def get_dimensions(self) -> dict:
        bounds = self.shape.bounds
        length = bounds[1][0] - bounds[0][0]
        width = bounds[1][1] - bounds[0][1]
        return {
            "length": round(length, 3),
            "width": round(width, 3),
            "units": self.shape.units,
        }

    def get_piercing_points(self) -> int:
        return len(self.shape.discrete)

    def save_preview_image(self, path: str = "preview.png", resolution=(100, 100)) -> None:
        image = self.shape.scene().save_image(resolution=resolution)
        with open(path, "wb") as f:
            f.write(image)

    def get_piercing_time(self) -> float:
        return self.get_piercing_points() * self.PIERCING_TIME

    def get_machinging_time(self) -> float:
        cutting_length_in_inches = self.get_cutting_length()
        piercing_count = self.get_piercing_points()

        total_time = piercing_count * self.PIERCING_TIME + cutting_length_in_inches * self.CUT_TIME_PER_INCH

        return round(total_time, 3)

    def get_machinging_time_minutes(self) -> float:
        return round(self.get_machinging_time() / 60.0, 2)

    def __str__(self):
        return f"""Cutting length: {self.get_cutting_length()} {self.get_units()}
Cutting area: {self.get_cutting_area()} {self.get_units()}^2
Cutting time: {self.get_machinging_time()} seconds
Cutting time: {self.get_machinging_time_minutes()} minutes
Units: {self.get_units()}
Dimensions: {self.get_dimensions()}
Piercing points: {self.get_piercing_points()}"""


if __name__ == "__main__":
    DXF_FILE = r"dxf test files/TP6A-20.dxf"

    analyzer = DxfAnalyzer(DXF_FILE)
    print(analyzer)
