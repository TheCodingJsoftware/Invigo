import os
import sys
from datetime import datetime

from utils.components_inventory.component import Component
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.quote.nest import Nest
from utils.quote.quote import Quote


class CoverPage:
    def __init__(self, title: str, quote: Quote) -> None:
        self.title = title
        self.quote = quote
        self.server_directory = f"http://{get_server_ip_address()}"

    def generate(self) -> str:
        return f"""<div id="cover-page">
                <label for="showCoverPage" id="showCoverPageLabel" style="background-color: #EAE9FC; width: 200px; margin-left: 84%; border: none; margin-top: 10px;">
                    Show Cover Page
                </label>
                <input style="background-color: #EAE9FC; display: none;" type="checkbox" id="showCoverPage" checked=true>
                <div style="position: absolute; top: 0;">
                    <img class="logo" src="{self.server_directory}/images/logo.png" alt="Logo">
                </div>
                <div class="title">
                    {self.title}
                </div>
                <div class="input-row" style="top: 60px; position: absolute; right: 0; width: 300px;">
                    <label>
                        Order #
                    </label>
                    <input type="text" class="input-box" id="order-number" value={self.quote.order_number}>
                </div>
                <div style="margin-bottom: 80px;">
                </div>
                <div class="date">
                    {str(datetime.now().strftime("%I:%M:%S %p %A %B %d, %Y"))}
                </div>
                <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; right: 0; width: 300px;height: 180px; position: absolute; margin: 10px; top: 100px;">
                    <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px">
                        Ship To:
                        <textarea style="resize: none;">{self.quote.ship_to}</textarea>
                    </div>
                </div>
                <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; left: 0; width: 400px; height: 180px; position: absolute; margin: 10px; top: 100px;">
                    <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px">
                        Date Shipped:
                        <input class="input-box" type="text" value="{self.quote.date_shipped}">
                        Date Expected:
                        <input class="input-box" type="text" value="{self.quote.date_expected}">
                        Received in good order by:
                        <input class="input-box" type="text" value="">
                    </div>
                </div>
                <div style="margin-bottom: 300px;">
            </div>
        </div>"""


class SheetsPictures:
    def __init__(self, nests: list[Nest]) -> None:
        self.nests = nests
        self.server_directory = f"http://{get_server_ip_address()}"

    def generate(self) -> str:
        sheets_picture_html = '<div class="nests">'
        for nest in self.nests:
            if nest.image_path != "images/404.jpeg":
                sheet_image_name = nest.name.replace(".pdf", "")
                sheets_picture_html += f'<div class="nest"><p>{sheet_image_name}</p><img src="{self.server_directory}/{nest.image_path}" alt="Sheet Image" class="nest_image" id="{sheet_image_name}"></div>'
        sheets_picture_html += "</div>"
        return sheets_picture_html


class SheetsTable:
    def __init__(self, nests: list[Nest]) -> None:
        self.headers = ["Sheet Name", "Thickness", "Materiak", "Dimension", "Scrap", "Qty", "Sheet Cut Time", "Nest Cut Time"]
        self.nests = nests
        self.grand_total_cut_time = 0.0

    def get_hours_minutes_seconds(self, total_seconds: float) -> tuple[int, int, int]:
        return int(total_seconds // 3600), int((total_seconds % 3600) // 60), int(total_seconds % 60)

    def get_total_sheet_count(self) -> int:
        return sum(nest.sheet_count for nest in self.nests)

    def generate(self) -> str:
        sheets_table_html = "<table class='ui-responsive' data-mode='' data-role='table' id='data-table-sheets' style='border-collapse: collapse; text-align: center; vertical-align: middle; font-size: 12px;'>"
        sheets_table_html += "<tr class='header-table-row'>"
        for header in self.headers:
            sheets_table_html += f"<th>{header}</th>"
        sheets_table_html += "</tr>"
        sheets_table_html += '<tbody id="table-body">'
        for nest in self.nests:
            single_hours, single_minutes, single_seconds = self.get_hours_minutes_seconds(nest.sheet_cut_time)
            nest_hours, nest_minutes, nest_seconds = self.get_hours_minutes_seconds(nest.get_machining_time())
            self.grand_total_cut_time += nest.get_machining_time()
            sheets_table_html += f"""<tr>
            <td>{nest.name}</td>
            <td>{nest.sheet.thickness}</td>
            <td>{nest.sheet.material}</td>
            <td>{nest.sheet.get_sheet_dimension()}</td>
            <td>{nest.scrape_percentage:,.2f}%</td>
            <td>{nest.sheet_count}</td>
            <td>{single_hours:02d}h {single_minutes:02d}m {single_seconds:02d}s</td>
            <td>{nest_hours:02d}h {nest_minutes:02d}m {nest_seconds:02d}s</td>
            </tr>"""

        grand_total_hours, grand_total_minutes, grand_total_seconds = self.get_hours_minutes_seconds(self.grand_total_cut_time)
        sheets_table_html += f"""<tr>
        <td>Total:</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td>{self.get_total_sheet_count()}</td>
        <td></td>
        <td>{grand_total_hours:02d}h {grand_total_minutes:02d}m {grand_total_seconds:02d}s</td>
        </tr>"""
        sheets_table_html += "</tbody></table>"
        return sheets_table_html


class LaserCutPartsTable:
    def __init__(self, title: str, laser_cut_parts: list[LaserCutPart]) -> None:
        self.title = title
        self.headers = [
            "Picture",
            "Part Name",
            "Material",
            "Thickness",
            "Qty",
            "Shelf #",
            "Unit Price",
            "Price",
        ]
        self.laser_cut_parts = laser_cut_parts
        self.server_directory = f"http://{get_server_ip_address()}"

    def generate_laser_cut_part_data(self, laser_cut_part: LaserCutPart) -> str:
        html = """<table class="dltrc" style="background:none;"><tbody>
                <tr class="dlheader" style="height: 20px;">
                    <td class="dlheader">Key</td>
                    <td class="dlheader">Value</td>
                </tr>"""
        for key, value in laser_cut_part.to_dict().items():
            html += f"""<tr class="dlinfo hover01" style="height: 20px;">
                <td class="dlinfo hover01">{key.replace("_", " ").title()}</td>
                <td class="dlinfo hover01">{value}</td>
                </tr>"""
        html += "</tbody></table>"
        return html

    def generate_laser_cut_part_popups(self):
        return "".join(
            f"""
                <div class="popup" id="{laser_cut_part.name}">
                    <div class="input-container-horizontal" style="padding: 5px; align-items: left; display: flex;">
                        <img src="{self.server_directory}/{laser_cut_part.image_index}" style="height: 100px; width: 100px;" alt="Laser Cut Part Image">
                        <h1 style="margin-left: 20px;">{laser_cut_part.name}</h1>
                        {self.generate_laser_cut_part_data(laser_cut_part)}
                    </div>
                    <a class="close-popup" href="#" onclick="clearImageBorders()">Close</a>
                    <br>
                    <br>
                </div>"""
            for laser_cut_part in self.laser_cut_parts
        )

    def get_total_cost(self) -> float:
        total = 0.0
        for laser_cut_part in self.laser_cut_parts:
            total += round(laser_cut_part.price, 2) * laser_cut_part.quantity
        return total

    def generate(self) -> str:
        html = '<table id="data-table-laser-cut_parts" data-role="table" data-mode="columntoggle" class="ui-responsive" style="border-collapse: collapse; text-align: center; vertical-align: middle;">'
        html += '<thead><tr class="header-table-row">'
        for i, header in enumerate(self.headers):
            is_visible = "visible"
            if self.title == "Quote" and header == "Shelf #":
                is_visible = "hidden"
            elif self.title == "Workorder" and header in ["Unit Price", "Price"]:
                is_visible = "hidden"
            html += f'<th data-priority="{i+1}" class="ui-table-cell-{is_visible}">{header}</th>'
        html += "</tr>"
        html += "</thead>"
        html += '<tbody id="table-body">'
        for laser_cut_part in self.laser_cut_parts:
            html += f"""<tr>
            <td class="ui-table-cell-visible">
                <div class="image-container">
                    <a class="popup-trigger" href="#{laser_cut_part.name}" onclick="highlightImage(\'{laser_cut_part.name}\', \'images/{laser_cut_part.name}\')">
                    <img src="{self.server_directory}/{laser_cut_part.image_index}" style="height: 60px; width: 60px;" alt="Laser Cut Part Image" id="images/{laser_cut_part.name}">
                </div>
            </td>
            <td class="ui-table-cell-visible">{laser_cut_part.name}</td>
            <td class="ui-table-cell-visible">{laser_cut_part.material}</td>
            <td class="ui-table-cell-visible">{laser_cut_part.gauge}</td>
            <td class="ui-table-cell-visible">{laser_cut_part.quantity}</td>
            <td class="ui-table-cell-{'visible' if self.title == "Workorder" else 'hidden'}">{laser_cut_part.shelf_number}</td>
            <td class="ui-table-cell-{'visible' if self.title == "Quote" else 'hidden'}">${laser_cut_part.price:,.2f}</td>
            <td class="ui-table-cell-{'visible' if self.title == "Quote" else 'hidden'}">${(laser_cut_part.price * laser_cut_part.quantity):,.2f}</td>
            </tr>"""
        html += f"""<tr>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td class="ui-table-cell-{'visible' if self.title == "Workorder" else 'hidden'}"></td>
            <td class="ui-table-cell-{'visible' if self.title == "Quote" else 'hidden'}"></td>
            <td class="ui-table-cell-{'visible' if self.title == "Quote" else 'hidden'}">Total: ${self.get_total_cost():,.2f}</td>
            </tr>"""
        html += "</tbody></table>"
        return html + self.generate_laser_cut_part_popups()


class ComponentsTable:
    def __init__(self, components: list[Component]) -> None:
        self.components = components
        self.server_directory = f"http://{get_server_ip_address()}"
        self.headers = ["Picture", "Part Name", "Part #", "Shelf #", "Qty", "Price"]

    def generate_components_data(self, component: Component) -> str:
        html = """<table class="dltrc" style="background:none;"><tbody>
                <tr class="dlheader" style="height: 20px;">
                    <td class="dlheader">Key</td>
                    <td class="dlheader">Value</td>
                </tr>"""
        for key, value in component.to_dict().items():
            html += f"""<tr class="dlinfo hover01" style="height: 20px;">
                <td class="dlinfo hover01">{key.replace("_", " ").title()}</td>
                <td class="dlinfo hover01">{value}</td>
                </tr>"""
        html += "</tbody></table>"
        return html

    def generate_components_popups(self):
        return "".join(
            f"""
                <div class="popup" id="{component.name}">
                    <div class="input-container-horizontal" style="padding: 5px; align-items: left; display: flex;">
                        <img src="{self.server_directory}/{component.image_path}" style="height: 100px; width: 100px;" alt="Component Image">
                        <h1 style="margin-left: 20px;">{component.part_name}</h1>
                        {self.generate_components_data(component)}
                    </div>
                    <a class="close-popup" href="#" onclick="clearImageBorders()">Close</a>
                    <br>
                    <br>
                </div>"""
            for component in self.components
        )

    def get_total_cost(self) -> float:
        total = 0.0
        for component in self.components:
            total += round(component.price, 2) * component.quantity
        return total

    def generate(self):
        html = '<table id="data-table-components" data-role="table" data-mode="columntoggle" class="ui-responsive" style="border-collapse: collapse; text-align: center; vertical-align: middle;">'
        html += '<thead><tr class="header-table-row">'
        for i, header in enumerate(self.headers):
            is_visible = "visible"
            if header == "Shelf #":
                is_visible = "hidden"
            html += f'<th data-priority="{i+1}" class="ui-table-cell-{is_visible}">{header}</th>'
        html += "</tr>"
        html += "</thead>"
        html += '<tbody id="table-body">'
        for component in self.components:
            html += f"""<tr>
            <td class="ui-table-cell-visible">
                <div class="image-container">
                    <a class="popup-trigger" href="#{component.name}" onclick="highlightImage(\'{component.name}\', \'images/{component.name}\')">
                    <img src="{self.server_directory}/{component.image_path}" style="height: 60px; width: 60px;" alt="Component Image" id="images/{component.name}">
                </div>
            </td>
            <td class="ui-table-cell-visible">{component.part_name}</td>
            <td class="ui-table-cell-visible">{component.part_number}</td>
            <td class="ui-table-cell-hidden">{component.shelf_number}</td>
            <td class="ui-table-cell-visible">{component.quantity}</td>
            <td class="ui-table-cell-visible">${component.price:,.2f}</td>
            </tr>"""
        html += f"""<tr>
        <td class="ui-table-cell-visible"></td>
        <td class="ui-table-cell-visible"></td>
        <td class="ui-table-cell-visible"></td>
        <td class="ui-table-cell-hidden"></td>
        <td class="ui-table-cell-visible"></td>
        <td class="ui-table-cell-visible">Total: ${self.get_total_cost():,.2f}</td>
        </tr>"""
        html += "</tbody></table>"
        return html + self.generate_components_popups()


class QuotePrintout:
    def __init__(self, quote: Quote) -> None:
        self.quote = quote

    def get_total_price(self) -> float:
        total = 0.0
        for component in self.quote.components:
            total += round(component.price, 2) * component.quantity
        for laser_cut_part in self.quote.grouped_laser_cut_parts:
            total += round(laser_cut_part.price, 2) * laser_cut_part.quantity
        return total

    def generate(self) -> str:
        html = ""
        if self.quote.nests:
            sheets_table = SheetsTable(self.quote.nests)
            sheets_pictures = SheetsPictures(self.quote.nests)
            html += '<details id="sheets-toggle" class="sheets-toggle">'
            html += '<summary style="font-size: 24px; text-align: center; margin-top: 20px;">Sheets/Nests</summary>'
            html += sheets_table.generate()
            html += sheets_pictures.generate()
            html += '<div class="page-break"></div>'
            html += "</details>"
        if self.quote.grouped_laser_cut_parts:
            html += '<h2 id="laser-cut-parts-heading">Laser Cut Parts</h2>'
            laser_cut_parts_table = LaserCutPartsTable("Quote", self.quote.grouped_laser_cut_parts)
            html += laser_cut_parts_table.generate()
        if self.quote.components:
            html += '<h2 id="components-heading">Components</h2>'
            components_table = ComponentsTable(self.quote.components)
            html += components_table.generate()
        if self.quote.grouped_laser_cut_parts or self.quote.components:
            html += f"""<label for="showTotalCost" id="showTotalCostLabel" style="background-color: #EAE9FC; width: 130px; margin-left: 44%; border: none;">Show Total Cost</label>
            <div id="total-cost-div">
                <input style="background-color: #EAE9FC; display: none;" type="checkbox" id="showTotalCost" checked>
                <h2 style="text-align: center; margin: 4px 0px;" id="total-cost">Total Cost: ${self.get_total_price():,.2f}</h2>
                <p style="text-align: center; text-decoration: underline; font-weight: bold;">No tax is included in this quote.</p>
                <p style="text-align: center;">Payment past due date will receive 1.5% interest rate per month of received goods.</p>
            </div>"""
        return html


class WorkorderPrintout:
    def __init__(self, quote: Quote) -> None:
        self.quote = quote

    def get_total_price(self) -> float:
        total = 0.0
        for component in self.quote.components:
            total += round(component.price, 2) * component.quantity
        for laser_cut_part in self.quote.grouped_laser_cut_parts:
            total += round(laser_cut_part.price, 2) * laser_cut_part.quantity
        return total

    def generate(self) -> str:
        html = ""
        if self.quote.nests:
            sheets_table = SheetsTable(self.quote.nests)
            sheets_pictures = SheetsPictures(self.quote.nests)
            html += '<details id="sheets-toggle" class="sheets-toggle" open="true">'
            html += '<summary style="font-size: 24px; text-align: center; margin-top: 20px;">Sheets/Nests</summary>'
            html += sheets_table.generate()
            html += sheets_pictures.generate()
            html += '<div class="page-break"></div>'
            html += "</details>"
        if self.quote.grouped_laser_cut_parts:
            html += '<h2 id="laser-cut-parts-heading">Laser Cut Parts</h2>'
            laser_cut_parts_table = LaserCutPartsTable("Workorder", self.quote.grouped_laser_cut_parts)
            html += laser_cut_parts_table.generate()
        if self.quote.components:
            html += '<h2 id="components-heading">Components</h2>'
            components_table = ComponentsTable(self.quote.components)
            html += components_table.generate()
        if self.quote.grouped_laser_cut_parts or self.quote.components:
            html += f"""<label for="showTotalCost" id="showTotalCostLabel" style="background-color: #EAE9FC; width: 130px; margin-left: 44%; border: none;">Show Total Cost</label>
            <div id="total-cost-div">
                <input style="background-color: #EAE9FC; display: none;" type="checkbox" id="showTotalCost">
                <h2 style="text-align: center; margin: 4px 0px;" id="total-cost">Total Cost: ${self.get_total_price():,.2f}</h2>
                <p style="text-align: center; text-decoration: underline; font-weight: bold;">No tax is included in this quote.</p>
                <p style="text-align: center;">Payment past due date will receive 1.5% interest rate per month of received goods.</p>
            </div>"""
        return html


class PackingSlipPrintout:
    def __init__(self, quote: Quote) -> None:
        self.quote = quote

    def get_total_price(self) -> float:
        total = 0.0
        for component in self.quote.components:
            total += round(component.price, 2) * component.quantity
        for laser_cut_part in self.quote.grouped_laser_cut_parts:
            total += round(laser_cut_part.price, 2) * laser_cut_part.quantity
        return total

    def generate(self) -> str:
        html = ""
        if self.quote.nests:
            sheets_table = SheetsTable(self.quote.nests)
            sheets_pictures = SheetsPictures(self.quote.nests)
            html += '<details id="sheets-toggle" class="sheets-toggle" open="false">'
            html += '<summary style="font-size: 24px; text-align: center; margin-top: 20px;">Sheets/Nests</summary>'
            html += sheets_table.generate()
            html += sheets_pictures.generate()
            html += '<div class="page-break"></div>'
            html += "</details>"
        if self.quote.grouped_laser_cut_parts:
            html += '<h2 id="laser-cut-parts-heading">Laser Cut Parts</h2>'
            laser_cut_parts_table = LaserCutPartsTable("Packing Slip", self.quote.grouped_laser_cut_parts)
            html += laser_cut_parts_table.generate()
        if self.quote.components:
            html += '<h2 id="components-heading">Components</h2>'
            components_table = ComponentsTable(self.quote.components)
            html += components_table.generate()
        if self.quote.grouped_laser_cut_parts or self.quote.components:
            html += f"""<label for="showTotalCost" id="showTotalCostLabel" style="background-color: #EAE9FC; width: 130px; margin-left: 44%; border: none;">Show Total Cost</label>
            <div id="total-cost-div">
                <input style="background-color: #EAE9FC; display: none;" type="checkbox" id="showTotalCost">
                <h2 style="text-align: center; margin: 4px 0px;" id="total-cost">Total Cost: ${self.get_total_price():,.2f}</h2>
                <p style="text-align: center; text-decoration: underline; font-weight: bold;">No tax is included in this quote.</p>
                <p style="text-align: center;">Payment past due date will receive 1.5% interest rate per month of received goods.</p>
            </div>"""
        return html


class GeneratePrintout:
    def __init__(
        self,
        title: str,
        quote: Quote,
    ) -> None:
        self.title = title
        self.quote = quote

        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        with open("utils/quote/quote.css", "r", encoding="utf-8") as quote_css_file:
            self.quote_css = quote_css_file.read()
        with open("utils/quote/quote.js", "r", encoding="utf-8") as quote_js_file:
            self.quote_js = quote_js_file.read()

    def generate(self) -> str:
        html = f"""<!DOCTYPE html>
                <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>{self.title} - {self.quote.name}</title>
                        <link rel="stylesheet" href="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css">
                        <script src="https://code.jquery.com/jquery-1.11.3.min.js"></script>
                        <script src="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
                    </head>
        <style>{self.quote_css}</style>
        <script>{self.quote_js}</script>
        <div data-role="page" id="pageone">"""

        cover_page = CoverPage(self.title, self.quote)

        html += cover_page.generate()

        if self.title == "Quote":
            quote_printout = QuotePrintout(self.quote)
            html += quote_printout.generate()
        elif self.title == "Workorder":
            workorder_printout = WorkorderPrintout(self.quote)
            html += workorder_printout.generate()
        elif self.title == "Packing Slip":
            packing_slip_printout = PackingSlipPrintout(self.quote)
            html += packing_slip_printout.generate()

        html += "</div>\n</html>"

        return html
