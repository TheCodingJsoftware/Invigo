import configparser
import json
import os
import sys
from datetime import datetime

from utils.quote_excel_file import ExcelFile
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class GenerateQuote:
    def __init__(self, action: tuple[bool, bool, bool, bool], quote_data: dict) -> None:
        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))

        config = configparser.ConfigParser()
        config.read(f"{self.program_directory}/laser_quote_variables.cfg")
        self.nitrogen_cost_per_hour: int = float(config.get("GLOBAL VARIABLES", "nitrogen_cost_per_hour"))
        self.co2_cost_per_hour: int = float(config.get("GLOBAL VARIABLES", "co2_cost_per_hour"))
        self.PROFIT_MARGIN: float = float(config.get("GLOBAL VARIABLES", "profit_margin"))
        self.OVERHEAD: float = float(config.get("GLOBAL VARIABLES", "overhead"))
        self.path_to_save_quotes = config.get("GLOBAL VARIABLES", "path_to_save_quotes")
        self.path_to_save_workorders = config.get("GLOBAL VARIABLES", "path_to_save_workorders")
        self.price_of_steel_information_path = config.get("GLOBAL VARIABLES", "price_of_steel_information")
        with open(self.price_of_steel_information_path, "r") as f:
            self.price_of_steel_information = json.load(f)
        self.path_to_sheet_prices = config.get("GLOBAL VARIABLES", "path_to_sheet_prices")
        with open(self.path_to_sheet_prices, "r") as f:
            self.sheet_prices = json.load(f)
        self.materials = config.get("GLOBAL VARIABLES", "materials").split(",")
        """
        SS      304 SS,409 SS   Nitrogen
        ST      Mild Steel      CO2
        AL      Aluminium       Nitrogen
        """
        self.gauges = config.get("GLOBAL VARIABLES", "gauges").split(",")

        self.file_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.quote_data = quote_data
        self.nests = self.get_nests()
        self.should_generate_quote, self.should_generate_workorder, self.should_update_inventory, self.should_generate_packing_slip = action
        if self.should_generate_quote or self.should_generate_packing_slip:
            self.generate_quote()
        if self.should_generate_workorder:
            self.generate_workorder()

    def generate_quote(self):
        """
        This function generates a quote by creating an Excel file with the given file name and path and
        then calling the generate method on it.
        """
        excel_document = ExcelFile(
            file_name=f"{self.path_to_save_quotes}/{self.file_name}.xlsx",
            generate_quote=True,
            should_generate_packing_slip=self.should_generate_packing_slip,
        )
        self.generate(excel_document)

    def generate_workorder(self):
        """
        This function generates a work order using an Excel file and saves it to a specified path.
        """
        excel_document = ExcelFile(
            file_name=f"{self.path_to_save_workorders}/{self.file_name}.xlsx",
            generate_quote=False,
            should_generate_packing_slip=self.should_generate_packing_slip,
        )
        self.generate(excel_document)

    def generate(self, excel_document: ExcelFile):
        """
        This function generates an Excel document with various data and tables based on input
        parameters.

        Args:
          excel_document (ExcelFile): The ExcelFile object that the function is generating data for and
        adding data to.
        """
        excel_document.add_list_to_sheet(cell="A1", items=self.materials)
        excel_document.add_list_to_sheet(cell="A2", items=self.gauges)
        excel_document.add_list_to_sheet(cell="A3", items=["Nitrogen", "CO2", "Packing Slip", "Quote", "Work Order"])
        excel_document.add_list_to_sheet(
            cell="A4",
            items=[self.nitrogen_cost_per_hour, self.co2_cost_per_hour],
        )
        excel_document.add_list_to_sheet(
            cell="A5",
            items=list(self.sheet_prices["Price Per Pound"].keys()),
        )
        excel_document.add_list_to_sheet(
            cell="A6",
            items=[self.sheet_prices["Price Per Pound"][sheet_name]["price"] for sheet_name in list(self.sheet_prices["Price Per Pound"].keys())],
        )

        excel_document.add_item_to_sheet(
            cell="A14",
            item=f"{len(self.nests)} files loaded",
        )
        excel_document.add_list_to_sheet(cell="A15", items=self.nests, horizontal=False)
        excel_document.add_list_to_sheet(
            cell=f"A{15+len(self.nests)}", items=["Gauge"] + list(self.price_of_steel_information["pounds_per_square_foot"].keys()), horizontal=True
        )
        excel_document.add_list_to_sheet(
            cell=f"A{16+len(self.nests)}", items=list(self.price_of_steel_information["pounds_per_square_foot"]["304 SS"].keys()), horizontal=False
        )
        temp_col = {0: "B", 1: "C", 2: "D", 3: "E", 4: "F", 5: "G", 6: "H"}
        for i, sheet_name in enumerate(list(self.price_of_steel_information["pounds_per_square_foot"].keys())):
            for j, thickness in enumerate(self.price_of_steel_information["pounds_per_square_foot"][sheet_name]):
                excel_document.add_item_to_sheet(
                    cell=f"{temp_col[i]}{16+len(self.nests)+j}", item=self.price_of_steel_information["pounds_per_square_foot"][sheet_name][thickness]
                )

        excel_document.add_image(cell="A1", path_to_image=f"{self.program_directory}/ui/logo.png")
        excel_document.set_cell_height(cell="A1", height=33)
        excel_document.set_cell_height(cell="A2", height=34)
        excel_document.set_cell_height(cell="A3", height=34)
        # if self.should_generate_quote:
        #     excel_document.add_item(cell="E1", item="Work Order")
        # else:
        #     excel_document.add_item(cell="E1", item="Packing Slip")
        excel_document.add_list(cell="A3", items=["Date Shipped:", ""])
        excel_document.add_list(cell="E2", items=["Order #", ""])
        excel_document.add_list(cell="E3", items=["Ship To:", ""])

        headers = [
            "Item",
            "Part name",
            "Material",
            "Thickness",
            "Qty",
            "Unit Price",
            "Price",
        ]

        excel_document.set_cell_width(cell="A1", width=15)
        excel_document.set_cell_width(cell="B1", width=22)
        excel_document.set_cell_width(cell="C1", width=13)
        excel_document.set_cell_width(cell="D1", width=12)
        excel_document.set_cell_width(cell="E1", width=10)
        excel_document.set_cell_width(cell="F1", width=12)
        excel_document.set_cell_width(cell="G1", width=12)

        if self.should_generate_packing_slip:
            excel_document.add_item("C2", f"{self.get_order_number()}")

        STARTING_ROW: int = 5
        nest_count_index: int = 0
        if self.should_generate_workorder:
            for nest in self.nests:
                excel_document.add_item(
                    cell=f"A{STARTING_ROW+nest_count_index}",
                    item=f"{nest.split('/')[-1].replace('.pdf', '')} - {self.quote_data[nest]['gauge']} {self.quote_data[nest]['material']} {self.quote_data[nest]['sheet_dim']} - Scrap: {self.quote_data[nest]['scrap_percentage']}% - Sheet Count: {self.quote_data[nest]['quantity_multiplier']}",
                )
                nest_count_index += 1
            excel_document.set_pagebreak(STARTING_ROW + nest_count_index)
            nest_count_index += 2
        excel_document.add_item(cell=f"H{nest_count_index+3}", item="Sheets:", totals=False)
        excel_document.add_item(cell=f"I{nest_count_index+3}", item=self.get_total_sheet_count(), totals=False)
        index: int = nest_count_index
        for item in list(self.quote_data.keys()):
            if item[0] == "_":
                continue
            row: int = index + STARTING_ROW
            excel_document.add_dropdown_selection(cell=f"C{row}", type="list", location="'info'!$A$1:$H$1")
            excel_document.add_dropdown_selection(cell=f"D{row}", type="list", location="'info'!$A$2:$K$2")

            excel_document.add_image(
                cell=f"A{row}",
                path_to_image=f"{self.program_directory}/images/{self.quote_data[item]['image_index']}.jpeg",
            )  # Image A
            excel_document.set_cell_height(cell=f"A{row}", height=78)
            excel_document.add_item(cell=f"B{row}", item=item)  # File name B
            excel_document.add_item(cell=f"C{row}", item=self.quote_data[item]["material"])  # Material Type C
            excel_document.add_item(cell=f"D{row}", item=self.quote_data[item]["gauge"])  # Gauge Selection D
            excel_document.add_item(cell=f"E{row}", item=self.quote_data[item]["quantity"])  # Quantity E
            excel_document.add_item(
                cell=f"F{row}",
                item=self.quote_data[item]["quoting_unit_price"],
                number_format="$#,##0.00",
            )  # quoting_unit_price F
            excel_document.add_item(
                cell=f"G{row}",
                item=self.quote_data[item]["quoting_price"],
                number_format="$#,##0.00",
            )  # quoting_price G

            index += 1
        STARTING_ROW += nest_count_index
        excel_document.add_table(
            display_name="Table1",
            theme="TableStyleLight8",
            location=f"A{STARTING_ROW-1}:G{index+STARTING_ROW-nest_count_index}",
            headers=headers,
        )
        index -= nest_count_index + 1
        excel_document.add_item(cell=f"A{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"B{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"C{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"D{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"E{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"F{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"R{index+STARTING_ROW+1}", item="Total:", totals=False)
        sheet_dim_left = f'TEXTAFTER("{self.quote_data[self.nests[0]]["sheet_dim"]}", " x ")'
        sheet_dim_right = f'TEXTBEFORE("{self.quote_data[self.nests[0]]["sheet_dim"]}", " x ")'
        price_per_pound = "INDEX(info!$A$6:$G$6,MATCH($E${6+nest_count_index}, info!$A$5:$G$5,0))"
        pounds_per_sheet = f"INDEX(info!$B${16+len(self.nests)}:$H${16+len(self.nests)+15},MATCH($F${6+nest_count_index},info!$A${16+len(self.nests)}:$A${16+len(self.nests)+15},0),MATCH($E${6+nest_count_index},info!$B${15+len(self.nests)}:$H${15+len(self.nests)},0))"
        sheet_quantity = f"Q{index+STARTING_ROW+1}"
        excel_document.add_item(
            cell=f"S{index+STARTING_ROW+1}",
            item=f"={sheet_dim_right}*{sheet_dim_left}/144*{price_per_pound}*{pounds_per_sheet}*{sheet_quantity}",
            number_format="$#,##0.00",
            totals=False,
        )
        excel_document.add_item(cell=f"G{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"F{index+STARTING_ROW+1}", item="Total: ", totals=True)
        excel_document.add_item(
            cell=f"G{index+STARTING_ROW+1}",
            item=f"=SUM(G{STARTING_ROW}:G{index+STARTING_ROW})",
            number_format="$#,##0.00",
            totals=True,
        )
        excel_document.add_item(cell=f"G{index+STARTING_ROW+2}", item="No Tax Included")
        if self.should_generate_quote:
            excel_document.add_item(
                cell=f"A{index+STARTING_ROW+2}",
                item="Payment past due date will receive 1.5% interest rate per month of received goods.",
            )
            excel_document.add_item(
                cell=f"A{index+STARTING_ROW+4}",
                item="Date expected:",
            )
            excel_document.add_item(
                cell=f"A{index+STARTING_ROW+6}",
                item="_______________________",
            )
            excel_document.add_item(
                cell=f"E{index+STARTING_ROW+4}",
                item="Received in good order by:",
            )
            excel_document.add_item(
                cell=f"E{index+STARTING_ROW+6}",
                item="______________________________",
            )

        if self.should_generate_quote:
            excel_document.set_print_area(cell=f"A1:G{index + STARTING_ROW+6}")
        else:
            excel_document.set_print_area(cell=f"A1:E{index + STARTING_ROW+1}")

        # excel_document.add_macro(macro_path=f"{self.program_directory}/macro.bin")
        """
        Macro Code:
        Private Sub Workbook_Open()
            Application.Iteration = True
            Application.MaxIterations = 1
        End Sub
        """

        if self.should_generate_workorder:
            excel_document.set_col_hidden("F1", True)
            excel_document.set_col_hidden("G1", True)
            excel_document.freeze_pane(STARTING_ROW)
        else:
            excel_document.freeze_pane(5)
        excel_document.save()

    def get_nests(self) -> list[str]:
        return [item for item in list(self.quote_data.keys()) if item[0] == "_"]

    def get_total_sheet_count(self) -> int:
        """
        This function returns the total sheet count by summing the quantity multiplier of each nest in
        the quote data.

        Returns:
          The function `get_total_sheet_count` is returning an integer value which is the sum of the
        `quantity_multiplier` values for all the nests in the `quote_data` dictionary.
        """
        return sum(self.quote_data[nest]["quantity_multiplier"] for nest in self.get_nests())

    def get_cutting_method(self, material: str) -> str:
        """
        "Given a material ID, return the cutting method."

        The first line of the function is a docstring. It's a string that describes what the function does.
        It's a good idea to include a docstring in every function you write

        Args:
        material_id (str): The material ID of the material you want to cut.

        Returns:
        The cutting method for the material.
        """
        with open(f"{self.program_directory}/material_id.json", "r") as material_id_file:
            data = json.load(material_id_file)
        return data[material]["cut"]

    def get_order_number(self) -> int:
        """
        This function retrieves an order number from a JSON file, increments it by 1, updates the JSON
        file with the new order number, and returns the original order number.

        Returns:
          an integer value which is the order number.
        """
        with open(settings_file.get_value("path_to_order_number")) as f:
            order_number_data = json.load(f)
        order_number: int = order_number_data["order_number"]
        settings_file.change_item("order_number", order_number + 1)
        order_number_data["order_number"] = order_number + 1
        with open(settings_file.get_value("path_to_order_number"), "w", encoding="utf-8") as json_file:
            json.dump(order_number_data, json_file, ensure_ascii=False, indent=4)
        return order_number
