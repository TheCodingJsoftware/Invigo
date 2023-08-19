from openpyxl import Workbook, load_workbook


class HistoryFile:
    """It's a wrapper around a file object that keeps track of the last line read"""

    def __init__(self) -> None:
        """
        It creates a workbook, creates two sheets, removes the default sheet, and then loads the file
        """
        self.file_name = "inventory history.xlsx"
        self.category_new_row_pos: int = 0
        self.single_item_new_row: int = 0
        try:
            self.workbook = load_workbook(f"data/{self.file_name}")
        except Exception:
            self.workbook = Workbook()
            self.workbook.create_sheet("Categories", 0)
            self.workbook.create_sheet("Single Items", 1)
            self.workbook.remove_sheet(self.workbook["Sheet"])
        self.categories_sheet = self.workbook["Categories"]
        self.single_items_sheet = self.workbook["Single Items"]
        self.category_data = {"Date": [], "Description": []}
        self.single_item_data = {"Date": [], "Description": []}
        self.load_file()

    def load_file(self) -> None:
        """
        It loads data from an excel file into a dictionary
        """
        self.category_new_row_pos = len(self.categories_sheet["A"])

        for cell in self.categories_sheet["A"]:
            self.category_data["Date"].append(cell.value)
        for cell in self.categories_sheet["B"]:
            self.category_data["Description"].append(cell.value)

        self.single_item_new_row = len(self.single_items_sheet["A"])

        for cell in self.single_items_sheet["A"]:
            self.single_item_data["Date"].append(cell.value)
        for cell in self.single_items_sheet["B"]:
            self.single_item_data["Description"].append(cell.value)

    def get_data_from_category(self) -> dict:
        """
        It returns the data from the category

        Returns:
          The category data
        """
        return self.category_data

    def get_data_from_single_item(self) -> dict:
        """
        It returns a dictionary of data from a single item

        Returns:
          The data from the single item.
        """
        return self.single_item_data

    def add_new_to_category(self, date: str, description: str) -> None:
        """
        It adds a new row to the categories sheet of the workbook, with the date and description of the
        new category

        Args:
          date (str): str
          description (str): str = "description"
        """
        self.categories_sheet.cell(
            row=self.category_new_row_pos + 1, column=1, value=date
        )
        self.categories_sheet.cell(
            row=self.category_new_row_pos + 1, column=2, value=description
        )
        self.workbook.save(f"data/{self.file_name}")

    def add_new_to_single_item(self, date: str, description: str) -> None:
        """
        It adds a new row to a sheet in an excel file

        Args:
          date (str): str
          description (str): str = "description"
        """
        self.single_items_sheet.cell(
            row=self.single_item_new_row + 1, column=1, value=date
        )
        self.single_items_sheet.cell(
            row=self.single_item_new_row + 1, column=2, value=description
        )
        self.workbook.save(f"data/{self.file_name}")
