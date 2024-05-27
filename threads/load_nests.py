import configparser
import io
import json
import os
import re
import shutil
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

from utils.components_inventory.components_inventory import ComponentsInventory
from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.quote.nest import Nest
from utils.quote.quote import Quote
from utils.sheet_settings.sheet_settings import SheetSettings


class LoadNests(QThread):
    signal = pyqtSignal(object)

    def __init__(self, parent, nests: list[str], components_inventory: ComponentsInventory, laser_cut_inventory: LaserCutInventory, sheet_settings: SheetSettings) -> None:
        QThread.__init__(self, parent)
        self.nests = nests
        self.data = {}

        self.components_inventory = components_inventory
        self.laser_cut_inventory = laser_cut_inventory
        self.paint_inventory = self.laser_cut_inventory.paint_inventory
        self.sheet_settings = sheet_settings

        self.quote = Quote("Quote", None, self.components_inventory, self.laser_cut_inventory, self.sheet_settings)

        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))

        config = configparser.ConfigParser()
        config.read(f"{self.program_directory}/laser_quote_variables.cfg")
        self.size_of_picture = int(config.get("GLOBAL VARIABLES", "size_of_picture"))

        # REGEX VARIABLEAS
        self.part_path_regex = config.get("REGEX", "part_path_regex", raw=True)
        self.machinging_time_regex = config.get("REGEX", "machinging_time_regex", raw=True)
        self.weight_regex = config.get("REGEX", "weight_regex", raw=True)
        self.surface_area_regex = config.get("REGEX", "surface_area_regex", raw=True)
        self.cutting_length_regex = config.get("REGEX", "cutting_length_regex", raw=True)
        self.quantity_regex = "  " + config.get("REGEX", "quantity_regex", raw=True)
        self.part_number_regex = config.get("REGEX", "part_number_regex", raw=True)
        self.sheet_quantity_regex = config.get("REGEX", "sheet_quantity_regex", raw=True)
        self.scrap_percentage_regex = config.get("REGEX", "scrap_percentage_regex", raw=True)
        self.piercing_time_regex = config.get("REGEX", "piercing_time_regex", raw=True)
        self.material_id_regex = config.get("REGEX", "material_id_regex", raw=True)
        self.gauge_regex = config.get("REGEX", "gauge_regex", raw=True)
        self.sheet_dimension_regex = config.get("REGEX", "sheet_dimension_regex", raw=True)
        self.part_dimensions_regex = config.get("REGEX", "part_dimension_regex", raw=True)
        self.piercing_points_regex = config.get("REGEX", "piercing_points_regex", raw=True)
        self.sheet_cut_time_regex = config.get("REGEX", "sheet_cut_time_regex", raw=True)
        self.geofile_name = config.get("REGEX", "geofile_name", raw=True)

    def extract_images_from_pdf(self, pdf_paths: list[str]) -> None:
        image_count: int = 0
        for _, pdf_path in enumerate(pdf_paths, start=1):
            pdf_file = fitz.open(pdf_path)
            for page_index in range(len(pdf_file)):
                page = pdf_file[page_index]
                if not (_ := page.get_images()):
                    continue
                for _, img in enumerate(page.get_images(), start=1):
                    xref = img[0]
                    base_image = pdf_file.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image = Image.open(io.BytesIO(image_bytes))
                    if image.size[0] == 48 and image.size[1] == 48:
                        continue
                    if image.size[0] == 580 and image.size[1] == 440:  # A nest picture
                        image.save(
                            open(
                                f"{self.program_directory}/images/nest-{image_count}.{image_ext}",
                                "wb",
                            )
                        )
                    else:  # A part picture
                        image = image.resize(
                            (self.size_of_picture, self.size_of_picture),
                            Image.Resampling.LANCZOS,
                        )
                        image.save(
                            open(
                                f"{self.program_directory}/images/part-{image_count}.{image_ext}",
                                "wb",
                            )
                        )

                    image_count += 1

    def convert_pdf_to_text(self, pdf_path: str) -> str:
        with open(f"{self.program_directory}/output.txt", "w", encoding="utf-8") as f:
            f.write("")

        pdf_file = fitz.open(pdf_path)
        pages = list(range(pdf_file.page_count))
        for pg in range(pdf_file.page_count):
            if pg in pages:
                page = pdf_file[pg]
                page_lines = page.get_text("text")
                with open(f"{self.program_directory}/output.txt", "a", encoding="utf-8") as f:
                    f.write(page_lines)

        with open(f"{self.program_directory}/output.txt", "r", encoding="utf-8") as f:
            all_text = f.read().replace(" \n", " ")

        with open(f"{self.program_directory}/output.txt", "w", encoding="utf-8") as f:
            f.write(all_text)
        return all_text

    def get_values_from_text(self, text: str, regex: str) -> any:
        matches = re.finditer(regex, text, re.MULTILINE)
        items = []
        for match in matches:
            if match.group(1) is None:
                items.append(match.group(2))
            else:
                items.append(match.group(1))
        return [items[0]] if len(items) == 1 else items

    def material_id_to_name(self, material: str) -> str:
        return self.sheet_settings.material_id["cutting_methods"][material]["name"]

    def material_id_to_number(self, number_id: str) -> str:
        return self.sheet_settings.material_id["thickness_ids"][number_id]

    def run(self) -> None:
        try:
            # try:
            #     shutil.rmtree(f"{self.program_directory}/images")
            # except:
            #     pass
            Path(f"{self.program_directory}/images").mkdir(parents=True, exist_ok=True)
            self.extract_images_from_pdf(self.nests)
            image_index: int = 0
            for nest in self.nests:
                # variables
                nest_name: str = os.path.basename(nest)
                nest_data = self.convert_pdf_to_text(nest)
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
                nest_object = Nest(
                    nest_name,
                    {
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
                # self.data[nest_name] = {}
                for i, part_name in enumerate(parts):
                    part_name = part_name.split("\\")[-1].replace("\n", "").replace(".GEO", "").replace(".geo", "").strip()
                    laser_cut_part = LaserCutPart(
                        part_name,
                        {
                            "quantity": int(quantities[i]),
                            "quantity_in_nest": int(quantities[i]),
                            "machine_time": float(machining_times[i]),
                            "weight": float(weights[i]),
                            "part_number": part_numbers[i],
                            "image_index": f"part-{image_index}",
                            "surface_area": float(surface_areas[i]),
                            "cutting_length": float(cutting_lengths[i]),
                            "file_name": nest,
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
                    # self.data[f"_{nest}"]["image_index"] = f"nest-{image_index}"
                    image_index += 1
            # os.remove(f"{self.program_directory}/output.txt")
            for nest in self.quote.nests:
                try:
                    image_name = nest.name.split("/")[-1].replace(".pdf", "")
                    image_path: str = f"images/{nest.image_path}.jpeg"
                    new_image_path = f"images/{image_name}.jpeg"
                    nest.image_path = new_image_path
                    shutil.move(image_path, new_image_path)
                except FileNotFoundError:
                    nest.image_path = "images/404.jpeg"
                for laser_cut_part in nest.laser_cut_parts:
                    image_path: str = f"images/{laser_cut_part.image_index}.jpeg"
                    new_image_path = f"images/{laser_cut_part.name}.jpeg"
                    laser_cut_part.image_index = new_image_path
                    shutil.move(image_path, new_image_path)

            self.quote.sort_nests()
            self.quote.sort_laser_cut_parts()
            # sorted_keys = natsorted(self.data.keys())
            # sorted_dict = {key: self.data[key] for key in sorted_keys}
            self.signal.emit(self.quote)
        except Exception as e:
            print(e)
            try:
                self.signal.emit(f"ERROR!\nException: {e}\nTrace stack:\n{traceback.print_exc()}\n\nIf the error still persists, send me an email of the pdf your trying nesting.\n{nest}")
            except Exception:
                self.signal.emit(f"ERROR!\nException: {e}\nTrace stack:\n{traceback.print_exc()}\n\nIf the error still persists, send me an email of the pdf your trying nesting.\n{self.nests[0]}")
