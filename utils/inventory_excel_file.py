from datetime import datetime

import xlsxwriter

from utils.json_file import JsonFile
from utils.settings import Settings

settings_file = Settings()


class ExcelFile:
    def __init__(self, inventory: JsonFile, file_name) -> None:
        self.file_name: str = file_name
        self.workbook: xlsxwriter.Workbook = xlsxwriter.Workbook(self.file_name)
        self.workbook.set_properties(
            {
                "title": "Inventory Manager",
                "subject": "Inventory",
                "author": "Jared Gross",
                "manager": "Jared Gross",
                "company": "TheCodingJ'software",
                "category": "Inventory Manager",
                "keywords": "Inventory, Manager, Inventory Manager",
                "comments": "Created with Python, Magic, XlsxWriter and most importantly, love.",
            }
        )
        self.table_headers = [
            "Part Name",
            "Part Number",
            "Unit Quantity",
            "Current Quantity",
            "Price",
        ]
        self.inventory = inventory

    def generate(self) -> None:
        """
        It takes a dictionary of dictionaries of dictionaries and writes it to an excel file.
        """
        data = self.inventory.get_data()
        text_format = self.workbook.add_format()
        text_format.set_text_wrap()
        text_format.set_align("center")
        text_format.set_align("vcenter")
        money_format = self.workbook.add_format({"num_format": "$#,##0.00"})
        money_format.set_align("center")
        money_format.set_align("vcenter")
        total_format = self.workbook.add_format({"num_format": "$#,##0.00"})
        self.set_cell_format(total_format)
        total_format_right = self.workbook.add_format({"num_format": "$#,##0.00"})
        self.set_cell_format(total_format_right)
        total_format_right.set_right(1)
        total_format_left = self.workbook.add_format({"num_format": "$#,##0.00"})
        self.set_cell_format(total_format_left)
        total_format_left.set_left(1)
        group_header_format = self.workbook.add_format(
            {
                "bottom": 2,
                "align": "center",
                "valign": "vcenter",
                "font_size": 18,
            }
        )
        for category in list(data.keys()):
            worksheet = self.workbook.add_worksheet(category.title())
            worksheet.set_header(f'&L{datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}&C&25{category.title()}&RPiney Manufacturing Inventory')
            worksheet.hide_gridlines(2)
            worksheet.set_margins(0.25, 0.25, 0.8, 0.25)
            # worksheet.freeze_panes("A2")
            worksheet.set_column("A:A", 45)
            worksheet.set_column("B:B", 16)
            worksheet.set_column("C:C", 12)
            worksheet.set_column("D:D", 15)
            worksheet.set_column("E:E", 10)
            row: int = 1
            grouped_category = self.__sort_groups(data[category])
            for group in list(grouped_category.keys()):
                starting_row: int = row
                worksheet.merge_range(f"A{row}:E{row}", group, group_header_format)
                worksheet.set_row(row - 1, 15)
                row += 1
                for item in list(grouped_category[group].keys()):
                    worksheet.write(row, 0, item, text_format)
                    worksheet.write(
                        row,
                        1,
                        grouped_category[group][item]["part_number"],
                        text_format,
                    )
                    worksheet.write(
                        row,
                        2,
                        grouped_category[group][item]["unit_quantity"],
                        text_format,
                    )
                    worksheet.write(
                        row,
                        3,
                        grouped_category[group][item]["current_quantity"],
                        text_format,
                    )
                    worksheet.write(row, 4, grouped_category[group][item]["price"], money_format)
                    worksheet.set_row(row, 50)

                    row += 1
                worksheet.add_table(
                    f"A{starting_row+1}:E{row}",
                    {
                        "style": "TableStyleLight8",
                        "first_column": False,
                        "columns": [{"header": header} for header in self.table_headers],
                    },
                )
                row += 1
            worksheet.write(row - 1, 0, "", total_format_left)
            worksheet.write(row - 1, 1, "", total_format)
            worksheet.write(row - 1, 2, "", total_format)
            worksheet.write(row - 1, 3, "Total Unit Cost:", total_format)
            worksheet.write(
                row - 1,
                4,
                self.inventory.get_total_unit_cost(category, self.__get_exchange_rate()),
                total_format_right,
            )
            worksheet.print_area(f"A1:E{row}")

    def set_cell_format(self, cell):
        cell.set_align("center")
        cell.set_align("vcenter")
        cell.set_bold()
        cell.set_top(6)
        cell.set_bottom(1)

    def __sort_groups(self, category: dict) -> dict:
        grouped_category: dict = {"Everything else": {}}

        for key, value in category.items():
            if group_name := value.get("group", ""):
                grouped_category.setdefault(group_name, {})
                grouped_category[group_name][key] = value
            else:
                grouped_category["Everything else"][key] = value

        return grouped_category

    def save(self) -> None:
        self.workbook.close()

    def __get_exchange_rate(self) -> float:
        return settings_file.get_value("exchange_rate")
