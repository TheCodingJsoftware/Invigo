import ezdxf
from ezdxf import recover
from ezdxf.addons.drawing import matplotlib

ezdxf.addons.drawing.properties.MODEL_SPACE_BG_COLOR = "#FFFFFF"
import math

"""
"quantity": DONE
"machine_time": CUTTING_LENGTH/100 (100 is 100 inches per minute cut time (roughly))
"weight": USER DETERMINED
"part_number": DONE
"image_index": DONE
"surface_area": ??????? USING PART_DIM????
"cutting_length": DONE
"file_name": DONE
"piercing_time": ???????????THE BOOK
"gauge": USER DETERMINED
"material": USER DETERMINED
"recut": DONE
"sheet_dim": DONE
"part_dim": USER DETERMINED,
"""


class DXF:
    """The class DXF is defined in Python."""

    def __init__(self, file_path: str) -> None:
        """
        This function initializes a class instance with various attributes related to a CAD file, such
        as part dimensions, surface area, entity types, cutting length, and thickness.

        Args:
          file_path (str): The file path of the DXF file that will be read and analyzed.
        """
        self.file_path = file_path
        self.doc = ezdxf.readfile(self.file_path)
        self.modelspace = self.doc.modelspace()

        self.part_dimension: str = self.get_part_dimensions()
        self.surface_area: float = self.get_surface_area()  # Aproximation, i.e., using part_dim
        self.entity_types: set[str] = self._get_entity_types()
        self.cutting_length: float = self.get_cutting_length()
        self.machine_time: float = self.cutting_length / 100
        self.thickness: float = self.get_thickness()

    def _get_entity_types(self) -> set[str]:
        """
        This function returns a set of entity types present in the modelspace.

        Returns:
          A set of strings representing the DXF types of all entities in the modelspace of the object.
        #"""
        entity_counts = {}
        for entity in self.modelspace:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

        return entity_counts

    def get_surface_area(self) -> float:
        """
        This function calculates the total surface area of all lines and arcs in a modelspace.

        Returns:
          the total surface area of all the lines and arcs in the modelspace of a DXF file. The surface
        area is calculated by multiplying the length of each line or arc by its thickness and summing up
        the results for all entities in the modelspace. The return value is a float representing the
        total surface area.
        """
        return math.prod([float(num) for num in self.part_dimension.split("x")])

    def get_thickness(self) -> float:
        """
        The function calculates the thickness of a 3D object by finding the difference between the
        minimum and maximum Z-coordinates of its lines.

        Returns:
          the thickness of the 3D object by calculating the difference between the maximum and minimum
        Z-coordinates of all the LINE entities in the modelspace. The returned value is a float
        representing the thickness of the object.
        """
        min_z = float("inf")
        max_z = float("-inf")

        # Iterate through the entities in the modelspace
        for entity in self.modelspace:
            if entity.dxftype() == "LINE":
                start_z = entity.dxf.start.z
                end_z = entity.dxf.end.z
                # Update the minimum and maximum Z-coordinates
                min_z = min(min_z, start_z, end_z)
                max_z = max(max_z, start_z, end_z)

        return max_z - min_z

    def get_cutting_length(self):
        """
        This function calculates the total perimeter of a set of lines and arcs in a modelspace.

        Returns:
          the total perimeter length of all the LINE and ARC entities in the modelspace of the AutoCAD
        drawing.
        """
        total_length = 0
        for entity in self.modelspace:
            if entity.dxftype() == "LINE":
                start_point = entity.dxf.start[:2]
                end_point = entity.dxf.end[:2]
                line_length = math.sqrt((end_point[0] - start_point[0]) ** 2 + (end_point[1] - start_point[1]) ** 2)
                total_length += line_length
            elif entity.dxftype() == "ARC":
                radius = entity.dxf.radius
                start_angle = math.degrees(entity.dxf.start_angle)
                end_angle = math.degrees(entity.dxf.end_angle)
                arc_length = abs(radius) * abs(end_angle - start_angle)
                total_length += arc_length
            elif entity.dxftype() == "CIRCLE":
                total_length += entity.dxf.radius * 2 * math.pi  # Formula: 2 * π * radius
            else:
                print(f"{entity.dxftype()} is not being calculated in cutting length")

        return total_length

    def get_part_dimensions(self) -> str:
        """
        The function calculates the dimensions of a part by iterating through its entities and finding
        the minimum and maximum x and y values of its lines.

        Returns:
          a string that represents the dimensions of a part. The string is in the format of "width x
        height", where width and height are the dimensions of the part in units determined by the
        drawing.
        """
        x_min = float("inf")
        y_min = float("inf")
        x_max = float("-inf")
        y_max = float("-inf")

        for entity in self.modelspace:
            if entity.dxftype() == "LINE":
                x1, y1 = entity.dxf.start[:2]
                x2, y2 = entity.dxf.end[:2]

                x_min = min(x_min, x1, x2)
                y_min = min(y_min, y1, y2)
                x_max = max(x_max, x1, x2)
                y_max = max(y_max, y1, y2)

        width = abs(x_max - x_min)
        height = abs(y_max - y_min)

        return f"{width}x{height}"

    def generate_thumbnail(self):
        self.doc, auditor = recover.readfile(self.file_path)
        if not auditor.has_errors:
            matplotlib.qsave(self.modelspace, "test.jpeg", params={"lineweight_scaling": 2}, dpi=300)


if __name__ == "__main__":
    dxf = DXF(r"dxf test files\12x12 PART.DXF")
    dxf.generate_thumbnail()
