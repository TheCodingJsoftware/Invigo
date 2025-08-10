import trimesh
from trimesh.path import Path2D


class DxfAnalyzer:
    def __init__(self, dxf_path: str):
        self.dxf_path = dxf_path
        self.shape = trimesh.load(dxf_path, force="2D")

        if not isinstance(self.shape, Path2D):
            raise ValueError("DXF did not load as a 2D shape")

    def get_cutting_length(self) -> float:
        total = 0.0
        for entity in self.shape.entities:
            try:
                total += entity.length(self.shape.vertices)
            except ValueError as e:
                if "colinear" in str(e):
                    print(f"Skipping invalid arc in {self.dxf_path}: {e}")
                    continue
                else:
                    raise
        return float(total)

    def get_cutting_area(self) -> float:
        return float(self.shape.area)

    def get_units(self) -> str:
        return str(self.shape.units)

    def get_dimensions(self) -> dict[str, float]:
        bounds = self.shape.bounds
        length = float(bounds[1][0] - bounds[0][0])
        width = float(bounds[1][1] - bounds[0][1])
        return {
            "length": round(length, 3),
            "width": round(width, 3),
            "units": self.shape.units,
        }

    def get_piercing_points(self) -> int:
        return len(self.shape.discrete)

    def save_preview_image(self, path: str = "images/preview.png", resolution=(100, 100)) -> None:
        try:
            if self.shape.bounds is None or (self.shape.bounds[1] - self.shape.bounds[0] == 0).all():
                print(f"[WARNING] Skipping preview rendering due to invalid bounds for {self.dxf_path}")
                return

            image = self.shape.scene().save_image(resolution=resolution)
            with open(path, "wb") as f:
                f.write(image)

        except Exception as e:
            print(f"[ERROR] Failed to render preview for {self.dxf_path}: {e}")

    def __str__(self):
        return f"""Cutting length: {self.get_cutting_length():,.2f} {self.get_units()}
Cutting area: {self.get_cutting_area():,.2f} {self.get_units()}^2
Units: {self.get_units()}
Dimensions: {self.get_dimensions()}
Piercing points: {self.get_piercing_points()}"""


if __name__ == "__main__":
    DXF_FILE = r"dxf test files/TP6A-20.dxf"

    analyzer = DxfAnalyzer(DXF_FILE)
    print(analyzer)
