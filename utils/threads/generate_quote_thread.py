import os
import shutil
import traceback
from pathlib import Path

from PyQt6.QtCore import pyqtSignal

from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.quote.quote import Quote
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.threads.load_nest_file_thread import LoadNestFileThread


class GenerateQuoteThread(LoadNestFileThread):
    signal = pyqtSignal(object)

    def __init__(
        self,
        parent,
        nest_files: list[str],
        components_inventory: ComponentsInventory,
        laser_cut_inventory: LaserCutInventory,
        sheet_settings: SheetSettings,
    ) -> None:
        super().__init__(parent, components_inventory, laser_cut_inventory, sheet_settings)
        self.nest_files = nest_files
        self.quote = Quote(
            "Quote",
            None,
            self.components_inventory,
            self.laser_cut_inventory,
            self.sheet_settings,
        )

    def run(self) -> None:
        try:
            Path(f"{self.program_directory}/images").mkdir(parents=True, exist_ok=True)
            self.extract_images_from_pdf(self.nest_files)
            image_index: int = 0
            for nest_file in self.nest_files:
                # variables
                nest_name: str = os.path.basename(nest_file)
                nest_data = self.convert_pdf_to_text(nest_file)
                quantity_multiplier: int = int(self.get_values_from_text(nest_data, self.sheet_quantity_regex)[0])
                scrap_percentage: float = float(self.get_values_from_text(nest_data, self.scrap_percentage_regex)[0])
                sheet_dimension: str = self.get_values_from_text(nest_data, self.sheet_dimension_regex)[0]
                sheet_material: str = self.material_id_to_name(self.get_values_from_text(nest_data, self.material_id_regex)[0])
                sheet_gauge: str = self.get_values_from_text(nest_data, self.gauge_regex)[0]
                sheet_cut_time: str = self.get_values_from_text(nest_data, self.sheet_cut_time_regex)[0]
                (
                    sheet_cut_time_hours,
                    sheet_cut_time_minutes,
                    sheet_cut_time_seconds,
                ) = sheet_cut_time.replace(
                    " : ", ":"
                ).split(":")
                total_sheet_cut_time = (float(sheet_cut_time_hours) * 3600) + (float(sheet_cut_time_minutes) * 60) + float(sheet_cut_time_seconds)  # seconds

                # lists
                _quantities: list[str] = self.get_values_from_text(nest_data, self.quantity_regex)
                quantities: list[int] = [int(quantity) for quantity in _quantities]
                machining_times: list[str] = self.get_values_from_text(nest_data, self.machinging_time_regex)
                weights: list[str] = self.get_values_from_text(nest_data, self.weight_regex)
                surface_areas: list[str] = self.get_values_from_text(nest_data, self.surface_area_regex)
                part_dimensions: list[str] = self.get_values_from_text(nest_data, self.part_dimensions_regex)
                cutting_lengths: list[str] = self.get_values_from_text(nest_data, self.cutting_length_regex)
                piercing_times: list[str] = self.get_values_from_text(nest_data, self.piercing_time_regex)
                part_numbers: list[str] = self.get_values_from_text(nest_data, self.part_number_regex)
                parts: list[str] = self.get_values_from_text(nest_data, self.part_path_regex)
                piercing_points: list[str] = self.get_values_from_text(nest_data, self.piercing_points_regex)
                geofile_names: list[str] = self.get_values_from_text(nest_data, self.geofile_name)
                # Sheet information:
                if int(sheet_gauge) >= 50:  # 1/2 inch
                    sheet_material = "Laser Grade Plate"
                sheet_gauge = self.material_id_to_number(sheet_gauge)
                nest_object = Nest({
                        "name": nest_name,
                        "sheet_count": quantity_multiplier,
                        "gauge": sheet_gauge,
                        "material": sheet_material,
                        "scrap_percentage": scrap_percentage,
                        "sheet_cut_time": total_sheet_cut_time,  # seconds
                        "image_path": f"nest-{image_index}",
                    },
                    self.sheet_settings,
                    self.laser_cut_inventory,
                )
                nest_object.sheet.length = float(sheet_dimension.strip().replace(" x ", "x").split("x")[0])
                nest_object.sheet.width = float(sheet_dimension.strip().replace(" x ", "x").split("x")[1])
                self.quote.add_nest(nest_object)
                for i, part_name in enumerate(parts):
                    part_name = part_name.split("\\")[-1].replace("\n", "").replace(".GEO", "").replace(".geo", "").strip()
                    laser_cut_part = LaserCutPart({
                            "name": part_name,
                            "quantity": int(quantities[i]),
                            "quantity_in_nest": int(quantities[i]),
                            "machine_time": float(machining_times[i]),
                            "weight": float(weights[i]),
                            "part_number": part_numbers[i],
                            "image_index": f"part-{image_index}",
                            "surface_area": float(surface_areas[i]),
                            "cutting_length": float(cutting_lengths[i]),
                            "file_name": nest_file,
                            "piercing_time": float(piercing_times[i]),
                            "piercing_points": int(piercing_points[i]),
                            "gauge": sheet_gauge,
                            "material": sheet_material,
                            "sheet_dim": sheet_dimension,
                            "part_dim": part_dimensions[i],
                            "geofile_name": geofile_names[i],
                        },
                        self.laser_cut_inventory,
                    )
                    laser_cut_part.nest = nest_object
                    nest_object.add_laser_cut_part(laser_cut_part)
                    image_index += 1
                if os.path.isfile(f"./images/nest-{image_index}.jpeg"):
                    nest_object.image_path = f"nest-{image_index}"
                    image_index += 1
            # os.remove(f"{self.program_directory}/output.txt")
            for nest_file in self.quote.nests:
                try:
                    image_name = nest_file.name.split("/")[-1].replace(".pdf", "")
                    image_path: str = f"images/{nest_file.image_path}.jpeg"
                    new_image_path = f"images/{image_name}.jpeg"
                    nest_file.image_path = new_image_path
                    shutil.move(image_path, new_image_path)
                except FileNotFoundError:
                    nest_file.image_path = "images/404.jpeg"
                for laser_cut_part in nest_file.laser_cut_parts:
                    image_path: str = f"images/{laser_cut_part.image_index}.jpeg"
                    new_image_path = f"images/{laser_cut_part.name}.jpeg"
                    laser_cut_part.image_index = new_image_path
                    shutil.move(image_path, new_image_path)

            self.quote.sort_nests()
            self.quote.sort_laser_cut_parts()
            self.signal.emit(self.quote)
        except Exception as e:
            print(e)
            try:
                self.signal.emit(f"ERROR!\nException: {e}\nTrace stack:\n{traceback.print_exc()}\n\nIf the error still persists, send me an email of the pdf your trying nesting.\n{nest_file}")
            except Exception:
                self.signal.emit(f"ERROR!\nException: {e}\nTrace stack:\n{traceback.print_exc()}\n\nIf the error still persists, send me an email of the pdf your trying nesting.\n{self.nest_files[0]}")
