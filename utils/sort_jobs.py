from openpyxl import load_workbook
from itertools import islice
import shutil
import os
import re
import tabula

import PyPDF2


def _make_name_safe(name: str):
    """
    The function replaces any invalid characters in a given string with underscores to make it safe for
    use as a directory name.

    Args:
      name (str): A string representing a directory name that needs to be made safe for use in a file
    system. The function replaces any invalid characters in the name with an underscore character.

    Returns:
      a string that is a safe version of the input `name` string, where any invalid characters (such as
    `<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, `*`) have been replaced with underscores (`_`).
    """
    invalid_chars_pattern = r'[<>:"/\\|?*]'

    safe_directory_name = re.sub(invalid_chars_pattern, "_", name)

    return safe_directory_name


def _find_column(path_to_excel_file: str, column_name_to_find: str) -> int:
    """
    This function finds the column number of a given column name in an Excel file.

    Args:
      path_to_excel_file (str): A string representing the file path to the Excel file that needs to be
    searched for the column.
      column_name_to_find (str): The name of the column that needs to be found in the Excel file.

    Returns:
      an integer representing the column number where the column_name_to_find is found in the first row
    of the worksheet. If the column_name_to_find is not found in the first row, the function returns
    None.
    """
    workbook = load_workbook(path_to_excel_file)
    worksheet = workbook.active

    try:
        for column, cell in enumerate(worksheet[1]):
            if column_name_to_find in cell.value:
                return column
    except TypeError:
        return -1
    return -1


def get_data_from_excel(path_to_excel_file: str) -> dict:
    """
    This function reads data from an Excel file and returns a dictionary of part names with their
    corresponding thickness.

    Args:
      path_to_excel_file (str): The path to the Excel file that contains the data to be extracted.

    Returns:
      a dictionary where the keys are part names and the values are their corresponding thicknesses,
    obtained from an Excel file specified by the input parameter `path_to_excel_file`.
    """
    workbook = load_workbook(filename=path_to_excel_file)
    worksheet = workbook.active
    part_names_new_with_thickness = {}
    part_name_column: int = _find_column(path_to_excel_file=path_to_excel_file, column_name_to_find="Part")
    material_column: int = _find_column(path_to_excel_file=path_to_excel_file, column_name_to_find="Material")
    thickness_column: int = _find_column(path_to_excel_file=path_to_excel_file, column_name_to_find="Thick")
    quantity_column: int = _find_column(path_to_excel_file=path_to_excel_file, column_name_to_find="Parts Per")
    if quantity_column == -1:
        quantity_column: int = _find_column(path_to_excel_file=path_to_excel_file, column_name_to_find="Qty")
    for row in islice(worksheet.iter_rows(values_only=True), 1, None):
        part_name: str = row[part_name_column]
        material: str = row[material_column]
        thickness: str = row[thickness_column]
        quantity: str = row[quantity_column]

        part_names_new_with_thickness[part_name] = {"thickness": _make_name_safe(str(thickness)), "quantity": quantity}

    return part_names_new_with_thickness


def get_data_from_pdf(path_to_pdf_file: str) -> dict:
    part_names_new_with_thickness = {}

    patterns = [
        r"(\d{1,2}) (\b[a-zA-Z0-9\-\|_]+\b)\s+(.*)     (.{1,9}) (\d{1,5}) (\d{1,5}\.\d{1,5})",  # 0
        r"(\d{1,2}) (\b[a-zA-Z0-9\-\|_]+\b)\s+(.*)     (.{1,9}) (\d{1,5}\.\d{1,5}) (\d{1,5})",  # 1
        r"^(\d+) (\d+) (\S+) (.*?) (\d+(?:\.\d+)?)?$",  # 2
        r"^(\d+) (\S+) (\d+\.\d+) (.*?) (\d+(?:\.\d+)?)?$",  # 3
    ]
    text = convert_pdf_to_text(pdf_path=path_to_pdf_file)

    matches = []
    for i, pattern in enumerate(patterns):
        if i == 0:
            matches = re.findall(pattern, text)
            if len(matches) < 2:
                continue
            for match in matches:
                item_no, part_name, material, thickness, quantity, weight = match
                part_names_new_with_thickness[part_name] = {"thickness": _make_name_safe(str(thickness)), "quantity": quantity, "material": material}
        elif i == 1:
            matches = re.findall(pattern, text)
            if len(matches) < 2:
                continue
            for match in matches:
                item_no, part_name, material, thickness, weight, quantity = match
                part_names_new_with_thickness[part_name] = {"thickness": _make_name_safe(str(thickness)), "quantity": quantity, "material": material}
        elif i == 2:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            if len(matches) < 2:
                continue
            for match in matches:
                if len(match) != 5 or match[4] == "" or len(match[2]) < 2:
                    continue
                item_no, quantity, part_name, material, thickness = match
                part_names_new_with_thickness[part_name] = {"thickness": _make_name_safe(str(thickness)), "quantity": quantity, "material": material}
        elif i == 3:
            for match in matches:
                if len(match) != 5 or match[4] == "" or len(match[2]) < 2:
                    continue
                item_no, quantity, part_name, material, thickness = match
                part_names_new_with_thickness[part_name] = {"thickness": _make_name_safe(str(thickness)), "quantity": quantity}

    return part_names_new_with_thickness


def convert_pdf_to_text(pdf_path: str) -> str:
    """
    This function converts a PDF file to text and removes extra spaces.

    Args:
        pdf_path (str): The file path of the PDF file that needs to be converted to text.
        progress_bar: It is a function that updates the progress bar to show the progress of the PDF
    to text conversion. It is called after each page is processed.
    """

    with open("output.txt", "w") as f:
        f.write("")

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        num_pages = len(reader.pages)

        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text = page.extract_text()

            # Identify table boundaries based on specific patterns or coordinates
            # Extract table content using string manipulation or regular expressions
            # Append extracted table data to the tables list

            with open("output.txt", "a") as f:
                f.write(text)

    with open("output.txt", "r") as f:
        all_text = f.read()

    with open("output.txt", "w") as f:
        f.write(all_text)
    return all_text


def get_all_file_paths_from_directory(directory_to_sort: str) -> list[str]:
    """
    This function retrieves all file paths from a given directory and its subdirectories.

    Args:
      directory_to_sort (str): A string representing the path of the directory from which we want to
    retrieve all file paths.

    Returns:
      a list of file paths (as strings) for all files in the directory and its subdirectories specified
    by the input parameter `directory_to_sort`.
    """
    file_paths = []
    for root, directories, files in os.walk(directory_to_sort):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths


def filter_file_paths(file_paths: list[str], desired_file_names: list[str]) -> list[str]:
    """
    This function filters a list of file paths based on a list of desired file names.

    Args:
      file_paths (list[str]): A list of file paths (strings) that you want to filter.
      desired_file_names (list[str]): The list of file names that we want to filter the file paths by.

    Returns:
      a list of file paths that match the desired file names.
    """
    filtered_paths = []
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        name_without_extension = os.path.splitext(file_name)[0]
        if name_without_extension in desired_file_names:
            filtered_paths.append(file_path)
    return filtered_paths


def sort_jobs(path_to_file: str, directory_to_sort: str, output_directory: str) -> None:
    """
    This function sorts files based on their extension and moves them to a new directory based on data
    obtained from an Excel file.

    Args:
      path_to_file (str): The path to the directory containing the files to be sorted, or the path to
    the Excel file containing the mapping of file names to their respective categories.
      output_directory (str): The output_directory parameter is a string that represents the path to the
    directory where the sorted files will be copied to.
    """
    data = {}
    if path_to_file.lower().endswith(".xlsx"):
        data = get_data_from_excel(path_to_file)
    elif path_to_file.lower().endswith(".pdf"):
        data = get_data_from_pdf(path_to_file)
    all_file_paths = get_all_file_paths_from_directory(directory_to_sort=directory_to_sort)
    filtered_paths = filter_file_paths(all_file_paths, list(data.keys()))
    new_copy_location = {}
    for file_path in filtered_paths:
        file_name: str = os.path.basename(file_path)
        name_without_extension: str = os.path.splitext(file_name)[0]
        extension: str = os.path.splitext(file_name)[1].replace(".", "").upper()
        quantity_mulitplier: str = f" x{data[name_without_extension]['quantity']}" if int(data[name_without_extension]["quantity"]) > 1 else ""
        new_copy_location[file_path] = {
            "new_location": f"{output_directory}\\{extension}\\{data[name_without_extension]['thickness']}",
            "old_name": f"{output_directory}\\{extension}\\{data[name_without_extension]['thickness']}\\{file_name}",
            "new_name": f"{output_directory}\\{extension}\\{data[name_without_extension]['thickness']}\\{name_without_extension}{quantity_mulitplier}{os.path.splitext(file_name)[1]}",
        }

    # copy_files(new_copy_location)


def copy_files(locations_dictionary: dict) -> None:
    """
    This function copies files from original locations to new locations and renames them if necessary.

    Args:
      locations_dictionary (dict): A dictionary containing information about the files to be copied. The
    keys are the original file locations, and the values are dictionaries containing the new location,
    old name, and new name of the file.
    """
    for original_location in locations_dictionary:
        new_location = locations_dictionary.get(original_location)["new_location"]
        old_name = locations_dictionary.get(original_location)["old_name"]
        new_name = locations_dictionary.get(original_location)["new_name"]
        os.makedirs(new_location, exist_ok=True)
        shutil.copy(original_location, new_location)
        if "DXF" in new_location:
            try:
                os.rename(old_name, new_name)
            except FileExistsError:
                os.remove(old_name)


if __name__ == "__main__":
    sort_jobs(
        path_to_file=r"C:\Users\jared\Downloads\Assy_SD10100.pdf",
        directory_to_sort=r"F:\Code\Python-Projects\Inventory Manager\test\OCFAB\Dumpsters",
        output_directory=r"C:\Users\jared\Downloads\I am Job Name",
    )
    print("done")
