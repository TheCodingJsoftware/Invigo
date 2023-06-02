import configparser
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path
import traceback

import fitz  # PyMuPDF
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal

from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class LoadNests(QThread):
    """
    Uploads client data to the server
    """

    signal = pyqtSignal(object)

    def __init__(self, parent, nests: list[str]) -> None:
        """
        The function is a constructor for a class that inherits from QThread. It takes a list of strings
        as an argument and returns None

        Args:
          file_to_upload (list[str]): list[str] = list of files to upload
        """
        QThread.__init__(self, parent)
        self.nests = nests
        self.data = {}

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

    def extract_images_from_pdf(self, pdf_paths: list[str]) -> None:
        """
        It opens a PDF file, extracts all the images from it, resizes them to a specific size, and saves
        them to a folder

        Args:
        pdf_paths (list): list = list of paths to the PDF files
        progress_bar: a function that prints a progress bar
        """
        image_count: int = 0
        for i, pdf_path in enumerate(pdf_paths, start=1):
            pdf_file = fitz.open(pdf_path)
            for page_index in range(len(pdf_file)):
                page = pdf_file[page_index]
                if not (image_list := page.get_images()):
                    continue
                for image_index, img in enumerate(page.get_images(), start=1):
                    xref = img[0]
                    base_image = pdf_file.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image = Image.open(io.BytesIO(image_bytes))
                    if image.size[0] == 48 and image.size[1] == 48:
                        continue
                    image = image.resize(
                        (self.size_of_picture, self.size_of_picture),
                        Image.Resampling.LANCZOS,
                    )
                    image.save(
                        open(
                            f"{self.program_directory}/images/{image_count}.{image_ext}",
                            "wb",
                        )
                    )
                    image_count += 1

    def convert_pdf_to_text(self, pdf_path: str) -> str:
        """
        This function converts a PDF file to text and removes extra spaces.

        Args:
          pdf_path (str): The file path of the PDF file that needs to be converted to text.
          progress_bar: It is a function that updates the progress bar to show the progress of the PDF
        to text conversion. It is called after each page is processed.
        """

        with open(f"{self.program_directory}/output.txt", "w") as f:
            f.write("")

        pdf_file = fitz.open(pdf_path)
        pages = list(range(pdf_file.page_count))
        for pg in range(pdf_file.page_count):
            if pg in pages:
                page = pdf_file[pg]
                page_lines = page.get_text("text")
                with open(f"{self.program_directory}/output.txt", "a") as f:
                    f.write(page_lines)

        with open(f"{self.program_directory}/output.txt", "r") as f:
            all_text = f.read().replace(" \n", " ")

        with open(f"{self.program_directory}/output.txt", "w") as f:
            f.write(all_text)
        return all_text

    def get_values_from_text(self, text: str, regex: str) -> any:
        """
        The function extracts values from a given text using a regular expression and returns them as a
        list.

        Args:
          text (str): The input text string that contains the values to be extracted using the regular
        expression.
          regex (str): The regular expression pattern to search for in the given text.

        Returns:
          a list of values extracted from the input text using the provided regular expression. If only
        one value is found, it is returned as a single-item list. If multiple values are found, they are
        returned as a list of items.
        """
        matches = re.finditer(regex, text, re.MULTILINE)
        items = []
        for match in matches:
            if match.group(1) is None:
                items.append(match.group(2))
            else:
                items.append(match.group(1))
        return [items[0]] if len(items) == 1 else items

    def material_id_to_name(self, material: str) -> str:
        """
        It opens the file material_id.json, loads the data, and returns the name of the material

        Args:
        material (str): The material ID of the material you want to convert.

        Returns:
        The name of the material.
        """
        with open(f"{self.program_directory}/material_id.json", "r") as material_id_file:
            data = json.load(material_id_file)
        return data[material]["name"]

    def material_id_to_number(self, number_id: str) -> str:
        """
        It takes a string as an argument, opens a json file, loads the data from the json file, and returns
        a string

        Args:
        number_id (str): The material ID number.

        Returns:
        The thickness of the material.
        """
        with open(f"{self.program_directory}/material_id.json", "r") as material_id_file:
            data = json.load(material_id_file)
        return data["thickness"][number_id]

    def run(self) -> None:
        """
        This is a Python function that extracts data from PDF files and stores it in a dictionary.
        """
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

                # lists
                _quantities: list[str] = self.get_values_from_text(nest_data, self.quantity_regex)
                quantities: list[int] = [int(quantity) * quantity_multiplier for quantity in _quantities]
                machining_times: list[str] = self.get_values_from_text(nest_data, self.machinging_time_regex)
                weights: list[str] = self.get_values_from_text(nest_data, self.weight_regex)
                surface_areas: list[str] = self.get_values_from_text(nest_data, self.surface_area_regex)
                part_dimensions: list[str] = self.get_values_from_text(nest_data, self.part_dimensions_regex)
                cutting_lengths: list[str] = self.get_values_from_text(nest_data, self.cutting_length_regex)
                piercing_times: list[str] = self.get_values_from_text(nest_data, self.piercing_time_regex)
                part_numbers: list[str] = self.get_values_from_text(nest_data, self.part_number_regex)
                parts: list[str] = self.get_values_from_text(nest_data, self.part_path_regex)
                # Sheet information:
                if int(sheet_gauge) >= 50:  # 1/2 inch
                    sheet_material = "Laser Grade Plate"
                sheet_gauge = self.material_id_to_number(sheet_gauge)
                self.data[f"_{nest}"] = {
                    "quantity_multiplier": quantity_multiplier,  # Sheet count
                    "gauge": sheet_gauge,
                    "material": sheet_material,
                    "sheet_dim": sheet_dimension,
                    "scrap_percentage": scrap_percentage,
                }
                self.data[nest_name] = {}
                for i, part_name in enumerate(parts):
                    part_name = part_name.split("\\")[-1].replace("\n", "").replace(".GEO", "").replace(".geo", "").strip()
                    self.data[nest_name][part_name] = {
                        "quantity": int(quantities[i]),
                        "machine_time": float(machining_times[i]),
                        "weight": float(weights[i]),
                        "part_number": part_numbers[i],
                        "image_index": image_index,
                        "surface_area": float(surface_areas[i]),
                        "cutting_length": float(cutting_lengths[i]),
                        "file_name": nest,
                        "piercing_time": float(piercing_times[i]),
                        "gauge": sheet_gauge,
                        "material": sheet_material,
                        "recut": False,
                        "sheet_dim": sheet_dimension,
                        "part_dim": part_dimensions[i],
                    }
                    image_index += 1
            # os.remove(f"{self.program_directory}/output.txt")
            for nest_name in list(self.data.keys()):
                if nest_name[0] == "_":
                    continue
                for item in list(self.data[nest_name].keys()):
                    image_path: str = f"images/{self.data[nest_name][item]['image_index']}.jpeg"
                    new_image_path = f"images/{item}.jpeg"
                    self.data[nest_name][item]["image_index"] = item
                    shutil.move(image_path, new_image_path)
            self.signal.emit(self.data)
        except Exception as e:
            print(e)
            try:
                self.signal.emit(
                    f"ERROR!\nException: {e}\nTrace stack:\n{traceback.print_exc()}\n\nIf the error still persists, send me an email of the pdf your trying nesting.\n{nest}"
                )
            except (UnboundLocalError, Exception):
                self.signal.emit(
                    f"ERROR!\nException: {e}\nTrace stack:\n{traceback.print_exc()}\n\nIf the error still persists, send me an email of the pdf your trying nesting.\n{self.nests[0]}"
                )
