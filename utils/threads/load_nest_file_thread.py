import io
import os
import re
import sys

import fitz  # PyMuPDF
from PIL import Image
from PyQt6.QtCore import QThread

from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.quote.quote import Quote
from utils.sheet_settings.sheet_settings import SheetSettings


class LoadNestFileThread(QThread):
    def __init__(
        self,
        parent,
        components_inventory: ComponentsInventory,
        laser_cut_inventory: LaserCutInventory,
        sheet_settings: SheetSettings,
    ) -> None:
        QThread.__init__(self, parent)
        self.parent = parent
        self.components_inventory = components_inventory
        self.laser_cut_inventory = laser_cut_inventory
        self.sheet_settings = sheet_settings

        self.quote = Quote(
            "Quote",
            None,
            self.components_inventory,
            self.laser_cut_inventory,
            self.sheet_settings,
        )

        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))

        self.size_of_picture = 100

        # REGEX VARIABLEAS
        self.part_path_regex = r"GEOFILE NAME: ([a-zA-z]:\\[\w\W]{1,300}\.[Gg][Ee][Oo])"
        self.machinging_time_regex = r"MACHINING TIME: (\d{1,}.\d{1,}) min"
        self.weight_regex = r"WEIGHT: (\d{1,}.\d{1,}) lb"
        self.surface_area_regex = r"SURFACE: (\d{1,}.\d{1,})  in2"
        self.cutting_length_regex = r"CUTTING LENGTH: (\d{1,}.\d{1,})  in|CUTTING LENGTH: (\d{1,})  in"
        self.quantity_regex = r"  NUMBER: (\d{1,})"
        self.part_number_regex = r"PART NUMBER: (\d{1,})"
        self.sheet_quantity_regex = r"PROGRAMME RUNS:  \/  SCRAP: (\d{1,})|PROGRAM RUNS:  \/  SCRAP: (\d{1,})"
        self.scrap_percentage_regex = r"PROGRAMME RUNS:  \/  SCRAP: \d{1,}  \/  (\d{1,}.\d{1,}) %|PROGRAM RUNS:  \/  SCRAP: \d{1,}  \/  (\d{1,}.\d{1,}) %"
        self.piercing_time_regex = r"PIERCING TIME (\d{1,}.\d{1,})  s"
        self.material_id_regex = r"MATERIAL ID \(SHEET\):.{1,}(ST|SS|AL)-\d{1,}"
        self.gauge_regex = r"MATERIAL ID \(SHEET\):.{1,}\w{2}-(\d{1,})"
        self.sheet_dimension_regex = r"BLANK: (\d{1,}\.\d{1,} x \d{1,}\.\d{1,}) x \d{1,}\.\d{1,}"
        self.part_dimensions_regex = r"DIMENSIONS: (\d{1,}\.\d{1,} x \d{1,}\.\d{1,})"
        self.piercing_points_regex = r"NUMBER OF PIERCING POINTS: (\d{1,})"
        self.sheet_cut_time_regex = r"MACHINING TIME: NC postprocessor (\d{1,} : \d{1,} : \d{1,})"
        self.geofile_name = r"GEOFILE NAME: (.:[\s\S]*?\.[Gg][Ee][Oo])"

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
