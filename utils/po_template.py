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
        self.signature: str = f"Lynden Gross                                                          {self.date}"
        self.vendor: str = self.get_vendor()
        self.order_number: int = self.get_order_number()
        self.order_number_cell = (4, 6)  # F4
        self.date_cell = (6, 6)  # F6

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
        Looks for what column the vendor is and grabs the first
        four rows below it.

        Returns:
          The value vendor.
        """
        workbook = load_workbook(filename=self.po_template)
        worksheet = workbook.active

        columns_to_search: list[str] = ["B", "C"]
        vendor_col: int = 0
        for column_number, column in enumerate(columns_to_search, start=1):
            for col in worksheet[column]:
                if col.value is None:
                    continue
                if "Vendor" in str(col.value):
                    vendor_col = column_number + 1  # They dont start at 0
        return " ".join(
            (
                str(worksheet.cell(row=row + 2, column=vendor_col).value)
                .replace("\n", " ")
                .replace("None", "")
                .replace("  ", " ")
            )
            for row in range(4)
        ).strip()

    def get_order_number(self) -> int:
        """
        It returns the order number from the excel file.

        Returns:
          The order number.
        """
        order_number: int = None
        workbook = load_workbook(filename=self.po_template)
        worksheet = workbook.active
        order_number = int(
            worksheet.cell(
                row=self.order_number_cell[0], column=self.order_number_cell[1]
            ).value
        )  # Merged: F4:G4
        # We only want to update the master templates PO number if it
        # was loaded from the templates directory, otherwise this is a new
        # file being added
        if "PO's" in self.po_template:
            worksheet.cell(
                row=self.order_number_cell[0], column=self.order_number_cell[1]
            ).value = (order_number + 1)
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
        worksheet.cell(
            row=self.order_number_cell[0], column=self.order_number_cell[1]
        ).value = (self.order_number + 1)
        workbook.save(self.output_path)

    def set_date(self) -> None:
        """
        It takes the excel file path, opens the file, finds the cell in the 6th row and 6th column, and
        sets the value of that cell to the date.
        """
        workbook = load_workbook(filename=self.output_path)
        worksheet = workbook.active
        worksheet.cell(row=self.date_cell[0], column=self.date_cell[1]).value = self.date
        workbook.save(self.output_path)

    def set_signature(self) -> None:
        """
        It opens an excel file, finds the row where the word "Authorized by" is, and then replaces the value in
        the cell in column 4 with the value of self.signature
        """
        workbook = load_workbook(filename=self.output_path)
        worksheet = workbook.active
        signature_row: int = 0
        for cell in worksheet["E"]:
            if cell.value is None:
                continue
            if "Authorized by" in str(cell.value):
                signature_row = cell.row - 1
        worksheet.cell(
            row=signature_row, column=5
        ).value = self.signature  # E:{signature_row}
        workbook.save(self.output_path)


if __name__ == "__main__":
    p = POTemplate(
        r"F:\Code\Python-Projects\Inventory Manager\Piney MFG\Cloverdale Paint\Clover Dale Paints PO#.xlsx"
    )
    print(p.get_vendor())
