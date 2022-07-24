import os
import shutil
from datetime import date

from openpyxl import load_workbook


class POTemplate:
    """It creates a class called POTemplate."""

    def __init__(self, po_template: str) -> None:
        """
        The function takes a string as an argument, and then sets the value of the class attributes to
        the values of the arguments

        Args:
          po_template (str): The path to the template file.
        """
        self.po_template = po_template
        self.cwd: str = os.path.abspath(os.getcwd()).replace("\\", "/")
        self.date = date.today().strftime("%m/%d/%y")
        self.signature: str = f"Lynden   Gross                                                                  {self.date}"
        self.vendor: str = self.get_vendor()
        self.order_number: int = self.get_order_number()

    def generate(self) -> None:
        """
        It copies a template file, sets the order number, date, and signature, and saves the file to a
        new location
        """
        self.output_path: str = (
            f"{self.cwd}/PO's/{self.vendor}/PO {self.order_number+1}.xlsx"
        )
        shutil.copyfile(self.po_template, self.output_path)
        self.set_order_number()
        self.set_date()
        self.set_signature()

    def get_vendor(self) -> str:
        """
        It opens an Excel file, reads the value of a cell, and returns it

        Returns:
          The value of the cell in the first row, second column.
        """
        workbook = load_workbook(filename=self.po_template)
        worksheet = workbook.active
        return str(worksheet.cell(row=2, column=3).value).replace("\n", " ")

    def get_order_number(self) -> int:
        """
        It returns the order number from the excel file.

        Returns:
          The order number.
        """
        order_number: int = None
        workbook = load_workbook(filename=self.po_template)
        worksheet = workbook.active
        order_number = int(worksheet.cell(row=4, column=6).value)
        worksheet.cell(row=4, column=6).value = order_number + 1
        workbook.save(self.po_template)
        return order_number

    def get_output_path(self) -> str:
        """
        This function returns the output path of the current instance of the class

        Returns:
          The output path
        """
        return self.output_path

    def set_order_number(self) -> None:
        """
        It takes the value of the cell in row 4, column 6, adds 1 to it, and then saves it back to the
        same cell.
        """
        workbook = load_workbook(filename=self.output_path)
        worksheet = workbook.active
        worksheet.cell(row=4, column=6).value = self.order_number + 1
        workbook.save(self.output_path)

    def set_date(self) -> None:
        """
        It takes the excel file path, opens the file, finds the cell in the 6th row and 6th column, and
        sets the value of that cell to the date.
        """
        workbook = load_workbook(filename=self.output_path)
        worksheet = workbook.active
        worksheet.cell(row=6, column=6).value = self.date
        workbook.save(self.output_path)

    def set_signature(self) -> None:
        """
        It opens an excel file, finds the row where the word "Lynden" is, and then replaces the value in
        the cell in column 4 with the value of self.signature
        """
        workbook = load_workbook(filename=self.output_path)
        worksheet = workbook.active
        signature_row: int = 0
        for cell in worksheet["E"]:
            if cell.value is None:
                continue
            if "Lynden" in cell.value:
                signature_row = cell.row
        worksheet.cell(row=signature_row, column=5).value = self.signature
        workbook.save(self.output_path)
