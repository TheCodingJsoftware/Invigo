import ezdxf
import trimesh
from rich import print
from trimesh.path import Path2D

DXF_FILE = r"dxf test files/TP6A-20.dxf"

shape = trimesh.load(DXF_FILE)
doc = ezdxf.readfile(DXF_FILE)


def extract_metadata(doc) -> dict:
    material = None
    thickness = None

    for layer in doc.layers:
        name = layer.dxf.name.lower()
        if "ss400" in name:
            material = "SS400"
        if "10g" in name:
            thickness = "10 gauge"

    return {"material": material, "thickness": thickness}


def extract_material_thickness_from_layers(doc):
    for layer in doc.layers:
        name = layer.dxf.name.lower()
        if "steel" in name or "aluminum" in name:
            # crude parsing: you can refine this
            parts = name.split("_")
            material = parts[0].capitalize()
            thickness = parts[1] if len(parts) > 1 else None
            return {"material": material, "thickness": thickness}
    return {"material": None, "thickness": None}


def get_part_dimensions_from_dxf(file_path: str) -> dict:
    shape = trimesh.load(file_path, force="2D")

    if not isinstance(shape, Path2D):
        raise ValueError("DXF did not load as a 2D shape")

    bounds = shape.bounds  # [[minx, miny], [maxx, maxy]]
    length = bounds[1][0] - bounds[0][0]
    width = bounds[1][1] - bounds[0][1]
    surface_area = length * width

    return {
        "length": round(length, 3),
        "width": round(width, 3),
        "surface_area": round(surface_area, 3),
    }


if isinstance(shape, trimesh.path.Path2D):
    print("Cutting length:", shape.length)
    print("Cutting area:", shape.area)
    print("Units:", shape.units)
    dimensions = get_part_dimensions_from_dxf(DXF_FILE)
    print(dimensions)
    print(extract_metadata(doc))
    print(extract_material_thickness_from_layers(doc))
    # Save preview image
    image = shape.scene().save_image(resolution=(512, 512))
    with open("preview.png", "wb") as f:
        f.write(image)
