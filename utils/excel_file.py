from datetime import datetime
from distutils.fancy_getopt import wrap_text

import xlsxwriter

from utils.json_file import JsonFile


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
        data = self.inventory.get_data()
        text_format = self.workbook.add_format()
        text_format.set_text_wrap()
        text_format.set_align("center")
        text_format.set_align("vcenter")
        money_format = self.workbook.add_format({"num_format": "$#,##0.00"})
        money_format.set_align("center")
        money_format.set_align("vcenter")
        total_format = self.workbook.add_format({"num_format": "$#,##0.00"})
        total_format.set_align("center")
        total_format.set_align("vcenter")
        total_format.set_bold()
        total_format.set_top(6)
        total_format.set_bottom(1)
        total_format_right = self.workbook.add_format({"num_format": "$#,##0.00"})
        total_format_right.set_align("center")
        total_format_right.set_align("vcenter")
        total_format_right.set_bold()
        total_format_right.set_top(6)
        total_format_right.set_bottom(1)
        total_format_right.set_right(1)
        total_format_left = self.workbook.add_format({"num_format": "$#,##0.00"})
        total_format_left.set_align("center")
        total_format_left.set_align("vcenter")
        total_format_left.set_bold()
        total_format_left.set_top(6)
        total_format_left.set_bottom(1)
        total_format_left.set_left(1)
        for index, category in enumerate(list(data.keys())):
            worksheet = self.workbook.add_worksheet(category.title())
            worksheet.set_header(
                f'&L{datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}&C&25{category.title()}&RPiney Manufacturing Inventory'
            )
            worksheet.hide_gridlines(2)
            worksheet.set_margins(0.25, 0.25, 0.8, 0.25)
            worksheet.freeze_panes("A2")
            worksheet.set_column("A:A", 45)
            worksheet.set_column("B:B", 16)
            worksheet.set_column("C:C", 12)
            worksheet.set_column("D:D", 15)
            worksheet.set_column("E:E", 10)
            for row, item in enumerate(list(data[category].keys())):
                worksheet.write(row, 0, item, text_format)
                worksheet.write(row, 1, data[category][item]["part_number"], text_format)
                worksheet.write(
                    row, 2, data[category][item]["unit_quantity"], text_format
                )
                worksheet.write(
                    row, 3, data[category][item]["current_quantity"], text_format
                )
                worksheet.write(row, 4, data[category][item]["price"], money_format)
                if row != 0:
                    worksheet.set_row(row, 50)
            worksheet.add_table(
                f"A1:E{row+1}",
                {
                    "style": "TableStyleLight8",
                    "first_column": False,
                    "columns": [{"header": header} for header in self.table_headers],
                },
            )
            worksheet.write(row + 1, 0, "", total_format_left)
            worksheet.write(row + 1, 1, "", total_format)
            worksheet.write(row + 1, 2, "", total_format)
            worksheet.write(row + 1, 3, "Unit Cost:", total_format)
            worksheet.write(
                row + 1,
                4,
                f"=SUMPRODUCT(Table{index+1}[[Unit Quantity]],Table{index+1}[[Price]])",
                total_format_right,
            )
            worksheet.print_area(f"A1:E{row+2}")

    def save(self) -> None:
        self.workbook.close()
