
import configparser
import os
import sys
from datetime import datetime

from bs4 import BeautifulSoup  # pip install beautifulsoup4

from utils.workspace.assembly import Assembly
from utils.workspace.item import Item


class AssemblyTable:
    def __init__(self, data: dict[Assembly, int]):
        self.headers = ['Assembly Name', 'Qty', 'Flow Tag']
        self.data = data

    def generate(self) -> str:
        html = "<table class='ui-responsive' data-mode='' data-role='table' id='data-table' style='border-collapse: collapse; text-align: center; vertical-align: middle; font-size: 12px;'>"
        html += "<tr class='header-table-row'>"
        for header in self.headers:
            html += f'<th>{header}</th>'
        html += '</tr>'
        html += '<tbody id="table-body">'
        for assembly, data in self.data.items():
            flow_tag = " ➜ ".join(assembly.assembly_data['flow_tag'])
            html += (
                '<tr>'
                f'<td class="ui-table-cell-visible">{assembly.name}</td>'
                f'<td class="ui-table-cell-visible">{data["quantity"]}</td>'
                f'<td class="ui-table-cell-visible">{flow_tag}</td>'
                '</tr>'
            )
        html += '</tbody></table>'
        return html


class ItemsTable:
    def __init__(self, assembly: Assembly, assembly_quantity: int, show_all_items: bool):
        self.headers = ['Part Name', 'Material', 'Thickness', 'Quantity', 'Notes', 'Flow Tags']
        self.assembly = assembly
        if show_all_items:
            self.items = assembly.get_all_items()
        else:
            self.items = assembly.items
        self.assembly_quantity = assembly_quantity

    def generate(self) -> str:
        html = "<table class='ui-responsive' data-mode='' data-role='table' id='data-table' style='border-collapse: collapse; text-align: center; vertical-align: middle; font-size: 12px;'>"
        html += "<tr class='header-table-row'>"
        for header in self.headers:
            html += f'<th>{header}</th>'
        html += '</tr>'

        html += '<tbody id="table-body">'
        for item in self.items:
            flow_tag = " ➜ ".join(item.data['flow_tag'])
            html += (
                '<tr>'
                f'<td class="ui-table-cell-visible">{item.name}</td>'
                f'<td class="ui-table-cell-visible">{item.data["material"]}</td>'
                f'<td class="ui-table-cell-visible">{item.data["thickness"]}</td>'
                f'<td class="ui-table-cell-visible">{item.data["parts_per"] * self.assembly_quantity}</td>'
                f'<td class="ui-table-cell-visible">{item.data["notes"]}</td>'
                f'<td class="ui-table-cell-visible">{flow_tag}</td>'
                '</tr>'
            )
        html += '</tbody></table>'
        return html

class GeneratePrintout:
    def __init__(self, filename: str, title: str, data: dict[Assembly, dict[dict[str, int], dict[str, bool]]], order_number: int) -> None:
        self.filename = filename
        self.title = title
        self.data = data
        self.order_number = order_number
        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        config = configparser.ConfigParser()
        config.read(f"{self.program_directory}/laser_quote_variables.cfg")
        self.path_to_save_printouts = config.get("GLOBAL VARIABLES", "path_to_save_workspace_printouts")


        with open('utils/workspace/printout.css', 'r') as printout_css_file:
            self.printout_css = printout_css_file.read()
        with open('utils/workspace/printout.js', 'r') as printout_js_file:
            self.printout_js = printout_js_file.read()


    def generate(self):
        assemblies_table = AssemblyTable(self.data)
        html_start = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>''' + self.title + '''</title>
            <link rel="stylesheet" href="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css">
            <script src="https://code.jquery.com/jquery-1.11.3.min.js"></script>
            <script src="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
        </head>
        <style> ''' + self.printout_css + '''</style>
        <script>''' + self.printout_js + '''</script>
        <div data-role="page" id="pageone">
            <div id="cover-page">
                <label for="showCoverPage" id="showCoverPageLabel" style="background-color: white; width: 200px; margin-left: 84%; border: none; margin-top: 10px;">
                 Show Cover Page
                </label>
                <input style="background-color: white; display: none;" type="checkbox" id="showCoverPage" checked=true>
                <div style="position: absolute; top: 0;">
                    <img class="logo" src="''' + self.program_directory + '''/icons/logo.png" alt="Logo">
                </div>
                <div class="title">''' + self.title + '''</div>
                <div class="input-row" style="top: 60px; position: absolute; right: 0; width: 300px;">
                    <label>
                    Order #
                    </label>
                    <input type="text" class="input-box" id="order-number">
                </div>
                <div style="margin-bottom: 80px;"></div>
                <div class="date"> ''' + str(datetime.now().strftime("%I:%M:%S %p %A %B %d, %Y")) + '''</div>
                <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; right: 0; width: 300px;height: 180px; position: absolute; margin: 10px; top: 100px;">
                    <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px">
                    Ship To:
                    <textarea style="resize: none;">




</textarea>
                    </div>
                </div>
                <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; left: 0; width: 400px; height: 180px; position: absolute; margin: 10px; top: 100px;">
                    <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px">
                    Date Shipped:
                        <input class="input-box" type="text" value=""></input>
                    Date Expected:
                    <input class="input-box" type="text" value=""></input>
                    Received in good order by:
                        <input class="input-box" type="text" value=""></input>
                    </div>
                </div>
                <div style="margin-bottom: 300px;">
                </div>
                </div>
        <div data-role="main" class="ui-content">
        '''
        html = html_start

        for assembly, data in self.data.items():
            parent_count = self.get_parent_assembly_count(assembly)
            if parent_count > 0:
                padding = 15 * parent_count
                html += f'<div style="padding: {padding}px;">'
            assembly_flow_tag = " -> ".join(assembly.assembly_data['flow_tag'])
            html += f'<div style="display: inline-flex; align-items: center;"><h2 style="margin-right: 15px;">{assembly.name} x {data["quantity"]}</h2> Assembly Flow Tag: {assembly_flow_tag}</div>'
            if len(assembly.items) > 0 and not data['show_all_items']:
                items_table = ItemsTable(assembly, data['quantity'], data['show_all_items'])
                html += items_table.generate()
            elif data['show_all_items']:
                items_table = ItemsTable(assembly, data['quantity'], data['show_all_items'])
                html += items_table.generate()
            if parent_count > 0:
                html += '</div>'
        # end
        html += '</div></html>'
        with open(f"{self.path_to_save_printouts}/{self.filename}.html", 'w') as f:
            f.write(BeautifulSoup(html, 'html.parser').prettify())

    def get_parent_assembly_count(self, starting_assembly: Assembly) -> int:
        count = 0
        assembly = starting_assembly
        while True:
            if assembly.parent_assembly is None:
                break
            assembly = assembly.parent_assembly
            count += 1
        return count
