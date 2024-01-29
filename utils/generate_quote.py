import configparser
import json
import os
import sys
from datetime import datetime

from bs4 import BeautifulSoup  # pip install beautifulsoup4

from utils.json_file import JsonFile
from utils.quote_excel_file import ExcelFile

settings_file = JsonFile(file_name="settings")


class GenerateQuote:
    def __init__(self, action: tuple[bool, bool, bool, bool, bool], file_name: str, quote_data: dict, order_number: int) -> None:
        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.order_number: int = order_number
        self.file_name = file_name
        config = configparser.ConfigParser()
        config.read(f"{self.program_directory}/laser_quote_variables.cfg")
        self.nitrogen_cost_per_hour: float = float(config.get("GLOBAL VARIABLES", "nitrogen_cost_per_hour"))
        self.co2_cost_per_hour: float = float(config.get("GLOBAL VARIABLES", "co2_cost_per_hour"))
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
        self.quote_data = quote_data
        self.nests = self.get_nests()
        self.should_generate_quote, self.should_generate_workorder, self.should_update_inventory, self.should_generate_packing_slip, self.should_group_items = action

        # if self.should_generate_quote:
        #     self.generate_quote()
        # elif self.should_generate_packing_slip:
        #     self.generate_packingslip()
        # if self.should_generate_workorder:
        #     self.generate_workorder()
        if self.should_generate_quote:
            self.generate_html(title="Quote")
        elif self.should_generate_packing_slip:
            self.generate_html(title="Packing Slip")
        if self.should_generate_workorder:
            self.generate_html(title="Workorder")

    def generate_html(self, title: str):
        sheets_html = "<table class='ui-responsive' data-mode='' data-role='table' id='data-table' style='border-collapse: collapse; text-align: center; vertical-align: middle; font-size: 12px;'><tr class='header-table-row'><th>Sheet Name</th><th>Thickness</th><th>Material</th><th>Dimension</th><th>Scrap</th><th>Qty</th><th>Cut Time</th></tr>"
        total_cuttime: float = 0

        for i, (item, item_data) in enumerate(self.quote_data.items()):
            if item[0] == '_':
                total_seconds = float(item_data['machining_time'])
                total_cuttime += total_seconds
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                sheet_name = item.split('/')[-1].replace('.pdf', '')
                
                # Add a new table row for each item
                sheets_html += (
                    f'<tr>'
                    f'<td>{sheet_name}</td>'
                    f'<td>{item_data["gauge"]}</td>'
                    f'<td>{item_data["material"]}</td>'
                    f'<td>{item_data["sheet_dim"]}</td>'
                    f'<td>{item_data["scrap_percentage"]}%</td>'
                    f'<td>{item_data["quantity_multiplier"]}</td>'
                    f'<td>{hours:02d}h {minutes:02d}m {seconds:02d}s</td>'
                    f'</tr>'
                )
        total_minutes = int((total_cuttime % 3600) // 60)
        total_seconds = int(total_cuttime % 60)
        total_hours = int(total_cuttime // 3600)
        sheets_html += (
            f'<tr>'
            f'<td></td>'
            f'<td></td>'
            f'<td></td>'
            f'<td></td>'
            f'<td></td>'
            f'<td>{self.get_total_sheet_count()}</td>'
            f'<td>{total_hours:02d}h {total_minutes:02d}m {total_seconds:02d}s</td>'
            f'</tr>'
            )

        sheets_html += "</table>"
        html_start = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>''' + title + '''</title>
            <link rel="stylesheet" href="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css">
            <script src="https://code.jquery.com/jquery-1.11.3.min.js"></script>
            <script src="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
        </head>
        <style>
            *{
                font-family: Verdana, Geneva, Tahoma, sans-serif;
            }
            html{
                background-color: white;
            }
            .ui-table{
                background-color: white;
            }
            .page{
                background-color: white;
            }
            .header-table-row{
                text-align: bottom;
                vertical-align: bottom;
                border: solid white 1px;
                border-bottom: 1px solid #ccc;
            }
            .ui-table th{
                vertical-align: bottom;
                text-align: center;
            }
            .ui-table tfoot tr td {
                vertical-align: top; /* Align content to the top */
                text-align: center; /* Horizontally center content */
            }
            .ui-table td{
                text-align: center;
                vertical-align: middle;
            }
            p{
                margin: 0px 0px;
            }

            /* Style for the title */
            .title {
                position: absolute;
                font-size: 34px;
                font-weight: bold;
                text-align: center;
                text-decoration: underline;
                width: 50%;
                top: 15px;
                position: absolute;
                left: 50%;
                -webkit-transform: translate(-50%,-50%);
                    -ms-transform: translate(-50%,-50%);
                        transform: translate(-50%,-50%);
            }


            /* Style for the date */
            .date {
                position: fixed;
                font-size: 10px;
                top: 0;
                right: 0;
            }
            body{
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                background-color: white;
            }
            .tg-wrap{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background-color: white;
            }

            .input-box{
                font-size: 16px;
            }
            .label {
                display: block;
                font-weight: bold;
            }

            .input-row {
                display: inline-flex;
                align-items: center;
                margin-bottom: 10px; /* Add spacing between rows */
            }

            .input-row label {
                flex: 0 0 auto;
                margin-right: 10px; /* Add spacing between label and input */
                width: auto; /* Set a fixed width for the label */
            }
            .ui-input-text{
                margin: 0;
            }
            th:first-of-type {
                border-top-left-radius: 10px;
            }
            th:last-of-type {
                border-top-right-radius: 10px;
            }
            tr:last-of-type td:first-of-type {
                border-bottom-left-radius: 10px;
            }
            tr:last-of-type td:last-of-type {
                border-bottom-right-radius: 10px;
            }
            tr {
                border: solid #ccc 1px;
            }
            /* Image and popup styles */
            .image-container {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .ui-table-cell-visible{
                padding: 0;
            }

            .popup-trigger {
            display: inline-block;
            transition: transform 0.2s;
            }

            .popup-trigger img {
                width: 300px;
                height: 300px;
                border: 2px solid transparent;
            }

            .popup {
                display: none;
                position: fixed;
                top: 0;
                right: 0;
                background-color: white;
                border: 1px solid #ccc;
                padding: 10px;
                width: auto;
                height: 100%;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                align-items: center;
                justify-content: center;
                z-index: 5;
                overflow-y: auto;
                overflow-x: hidden;
            }

            .popup:target {
            display: block;
            }

            .image-container:target {
                border-color: green;
            }

            .popup-trigger:hover {
                transform: scale(1.1);
                filter: sepia(0.3);
            }
            .popup-trigger:active {
                transform: scale(0.9);
                filter: sepia(0.6);
            }

            .close-popup {
                display: block;
                text-align: right;
                cursor: pointer;
                color: #333;
            }
            /* Styling the label to look like an "X" button */
            .close-popup::before {
                font-size: 18px;
                color: #333;
            }
            #sheets-toggle {
                cursor: pointer;
            }
            th:first-of-type {
            border-top-left-radius: 10px;
            }
            th:last-of-type {
                border-top-right-radius: 10px;
            }
            tr:last-of-type td:first-of-type {
                border-bottom-left-radius: 10px;
            }
            tr:last-of-type td:last-of-type {
                border-bottom-right-radius: 10px;
            }
            table.dltrc {
                width: 95%;
                border-collapse: separate;
                border-spacing: 0px;
                border: solid #ccc 2px;
                border-radius: 8px;
            }

            tr.dlheader {
                text-align: center;
                font-weight: bold;
                border-left: solid #ccc 1px;
                padding: 2px
            }

            td.dlheader {
                background: #d9d9d9;
                text-align: center;
                font-weight: bold;
                border-left: solid #ccc 1px;
                border-radius: 0px;
                padding: 2px
            }

            tr.dlinfo,
            td.dlinfo {
                text-align: center;
                border-left: solid #ccc 1px;
                border-top: solid #ccc 1px;
                padding: 2px
            }

            td.dlinfo:first-child,
            td.dlheader:first-child {
                border-left: none;
            }

            td.dlheader:first-child {
                border-radius: 5px 0 0 0;
            }

            td.dlheader:last-child {
            border-radius: 0 5px 0 0;
            }
            .ui-page{
                background-color: white;
            }
            .ui-btn{
                background-color: white;
            }
            @media print{
                .ui-table-columntoggle-btn{
                    display: none;
                }
                .page-break {
                    page-break-after: always;
                }
            }
        </style>
            <script>
                window.addEventListener("beforeprint", function() {
                    adjustTableOffsets();
                });

                window.addEventListener("afterprint", function() {
                    // Code to reset table offsets after print preview
                    resetTableOffsets();
                });
                function adjustTableOffsets() {
                    var headerRows = document.querySelectorAll("thead tr");
                    var checkbox = document.getElementById("showTotalCost");
                    var checkboxLabel = document.getElementById("showTotalCostLabel");
                    var checkboxCoverPageLabel = document.getElementById("showCoverPageLabel");
                    var checkboxCoverPage = document.getElementById("showCoverPage");
                    var total_cost_div = document.getElementById("total-cost-div");
                    var cover_page_div = document.getElementById("cover-page");
                    if (checkbox.checked) {
                        total_cost_div.style.display = "block";
                    } else {
                        total_cost_div.style.display = "none";
                    }
                    if (checkboxCoverPage.checked) {
                        cover_page_div.style.display = "block";
                    } else {
                        cover_page_div.style.display = "none";
                    }
                    checkbox.style.display = "none";
                    checkboxLabel.style.display = "none";
                    checkboxCoverPageLabel.style.display = "none";
                    for (var i = 0; i < headerRows.length; i++) {
                        headerRows[i].style.height = "50px";
                    }
                    const detailsElement = document.getElementById("sheets-toggle");
                    if (detailsElement.open) {
                        detailsElement.style.display = "block";
                    } else {
                        detailsElement.style.display = "none";
                    }
                }
                function resetTableOffsets() {
                    const detailsElement = document.getElementById("sheets-toggle");
                    detailsElement.style.display = "block";
                    var checkboxLabel = document.getElementById("showTotalCostLabel");
                    var checkboxCoverPageLabel = document.getElementById("showCoverPageLabel");
                    var total_cost_div = document.getElementById("total-cost-div");
                    var cover_page_div = document.getElementById("cover-page");
                    total_cost_div.style.display = "block";
                    cover_page_div.style.display = "block";
                    checkboxLabel.style.display = "block";
                    checkboxCoverPageLabel.style.display = "block";
                }
                function clearImageBorders(){
                    window.location.href = "";
                    const allImages = document.querySelectorAll('.popup-trigger img');
                    allImages.forEach(image => {
                        image.style.border = '2px solid transparent';
                        image.style.borderRadius  = '0';
                        image.style.filter = 'sepia(0)';
                    });
                }
                function highlightImage(imageName, imageId) {
                    const allImages = document.querySelectorAll('.popup-trigger img');
                    allImages.forEach(image => {
                        image.style.border = '2px solid transparent';
                        image.style.borderRadius  = '0';
                        image.style.filter = 'sepia(0)';
                    });
                        window.location.href = "#" + imageName;

                        const image = document.getElementById(imageId);
                        image.style.border = '2px solid lime';
                        image.style.borderRadius  = '5px';
                        image.style.filter = 'sepia(1)';
                    }

            </script>
        <div data-role="page" id="pageone">
            <div id="cover-page">
                <label for="showCoverPage" id="showCoverPageLabel" style="background-color: white; width: 200px; margin-left: 84%; border: none; margin-top: 10px;">
                 Show Cover Page
                </label>
                <input style="background-color: white; display: none;" type="checkbox" id="showCoverPage" checked=true>
                <div style="position: absolute; top: 0;">
                    <img class="logo" src="''' + self.program_directory + '''/icons/logo.png" alt="Logo">
                </div>
                <div class="title">''' + title + '''</div>
                <div class="input-row" style="top: 60px; position: absolute; right: 0; width: 300px;">
                    <label>
                    Order #
                    </label>
                    <input type="text" class="input-box" id="order-number" ''' + (f'value="{self.order_number if title == "Packing Slip" else ""}"') + '''>
                </div>
                <div style="margin-bottom: 80px;"></div>
                <div class="date"> ''' + str(datetime.now().strftime("%I:%M:%S %p %A %B %d, %Y")) + '''</div>
                <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; right: 0; width: 300px;height: 150px; position: absolute; margin: 10px; top: 100px;">
                    <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px"> 
                        Ship To:
                        <div style="height: 30px; border-top: #cccccc; border-top-width: 1px; border-top-style: solid"></div>
                        <div style="height: 30px; border-top: #cccccc; border-top-width: 1px; border-top-style: solid"></div>
                        <div style="height: 30px; border-top: #cccccc; border-top-width: 1px; border-top-style: solid"></div>
                        <div style="height: 30px; border-top: #cccccc; border-top-width: 1px; border-top-style: solid"></div>
                    </div>
                </div>
                <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; left: 0; width: 400px; height: 150px; position: absolute; margin: 10px; top: 100px;">
                <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px"> 
                        Date Shipped:
                        <div style="height: 15px; border-top: #cccccc; border-top-width: 1px; border-top-style: solid"></div>
                        Date Expected:
                        <div style="height: 15px; border-top: #cccccc; border-top-width: 1px; border-top-style: solid"></div>
                        Received in good order by:
                        <div style="height: 30px; border-top: #cccccc; border-top-width: 1px;"></div>
                        <div style="height: 30px; border-top: #cccccc; border-top-width: 1px; border-top-style: solid"></div>
                    </div>
                </div>
                <div style="margin-bottom: 300px;"></div>
            </div>
        <details id="sheets-toggle" class="sheets-toggle" ''' + ("open=\"true\"" if title == "Workorder" else "") + '''>
            <summary style="font-size: 24px; text-align: center; margin-top: 20px;">Sheets/Nests/Assemblies:</summary>
            ''' + sheets_html + '''
            <div class="page-break"></div>
        </details>
        <div data-role="main" class="ui-content">
        '''

        html_end = f'''
        </div style="width: 60%;">
            <label for="showTotalCost" id="showTotalCostLabel" style="background-color: white; width: 130px; margin-left: 44%; border: none;">Show Total Cost</label>
            <div id="total-cost-div">
            ''' + (f'<input style="background-color: white; display: none;" type="checkbox" id="showTotalCost" {"checked=true" if title == "Quote" else ""}>') + '''
            ''' + (f'<h2 style="text-align: center; margin: 4px 0px;" id="total-cost">Total Cost: ${self.get_total_price():,.2f}</h2>') + '''
            <p style="text-align: center; text-decoration: underline; font-weight: bold;">No tax is added in this quote.</p>
            <p style="text-align: center;">Payment past due date will receive 1.5% interest rate per month of received goods.</p>
        </div>
        </html>'''
        html_text = html_start
        if self.should_group_items:
            for i1, nest in enumerate(list(self.quote_data.keys())):
                if nest[0] == '_' or nest == "Components":
                    continue
                has_items: bool = False
                if i1 >= 1:
                    html_text += '<div class="page-break"></div>'
                html_text += f"<h2 style='text-align: center'>{nest.replace('.pdf', '')}</h2><br>"
                for i, (item, item_data) in enumerate(self.quote_data[nest].items()):
                    if nest[0] != '_' and nest != "Components":
                        if i == 0:
                            html_text += '''<table id="data-table" data-role="table" data-mode="columntoggle" class="ui-responsive" style="border-collapse: collapse; text-align: center; vertical-align: middle;"><thead><tr class="header-table-row"><th data-priority="1" class="ui-table-cell-visible">Picture</th><th data-priority="2" class="ui-table-cell-visible">Part Name</th><th data-priority="7" class="''' + ("ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible") + '''">Shelf Number</th><th data-priority="6" class="ui-table-cell-visible">Material</th><th data-priority="5" class="ui-table-cell-visible">Thickness</th><th data-priority="4" class="ui-table-cell-visible">Quantity</th><th data-priority="10" class="''' + ("ui-table-cell-visible" if title == "Workorder" else "ui-table-cell-hidden") + '''">Notes</th><th data-priority="9" class="''' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + '''">Unit Price</th><th data-priority="3" class="''' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + '''">Price</th></tr></thead><tbody id="table-body">'''
                            has_items = True
                        html_item_data = '<table class="dltrc" style="background:none;"><tbody><tr class="dlheader" style="height: 20px;"><td class="dlheader">Key</td><td class="dlheader">Value</td></tr>'
                        for data in item_data:
                            html_item_data += f'<tr class="dlinfo hover01" style="height: 20px;"><td class="dlinfo hover01">{data.replace("_", " ").title()}</td><td class="dlinfo hover01"> {item_data[data]}</td></tr>'
                        else:
                            html_item_data += '</tbody></table>'
                        try:
                            shelf_number = item_data["shelf_number"]
                        except KeyError:
                            shelf_number = ""
                        try:
                            flow_tag = " -> ".join(item_data["flow_tag"]) + '<br>'
                        except KeyError:
                            flow_tag = ""
                        try:
                            notes = f"{flow_tag}{item_data['notes']}"
                        except KeyError:
                            notes = f"{flow_tag}"
                        try:
                            html_text += f'<tr><td class="ui-table-cell-visible"><div class="image-container"><a class="popup-trigger" href="#{item}" onclick="highlightImage(\'{item}\', \'images/{item}.jpeg\')"><img src="{self.program_directory}/images/{item}.jpeg" style="height: 60px; width: 60px;" alt="Image" id="images/{item}.jpeg"></a><div class="popup" id="{item}"><div class="input-container-horizontal" style="padding: 5px; align-items: left; display: flex;"><img src="{self.program_directory}/images/{item}.jpeg" style="height: 100px; width: 100px;" alt="Image"><h1 style="margin-left: 20px;">{item}</h1></div>{html_item_data}<a class="close-popup" href="#" onclick="clearImageBorders()">Close</a></div></div></td><td class="ui-table-cell-visible">{item}</td><td class="{"ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible"}">{shelf_number}</td><td class="ui-table-cell-visible">{item_data["material"]}</td><td class="ui-table-cell-visible">{item_data["gauge"]}</td><td class="ui-table-cell-visible">{item_data["quantity"]}</td><td class="{"ui-table-cell-visible" if title == "Workorder" else "ui-table-cell-hidden"}">{notes}</td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}">{item_data["unit_price"]}</td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}">{item_data["price"]}</td></tr>\n'
                        except KeyError as e:
                            print(f"Key Error for {e}")
                            continue
                else:
                    if has_items:
                        html_text += f'<tr style="height: 20px;"><td class="ui-table-cell-visible"></td><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible"}"></td><td class="ui-table-cell-visible"></td><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-visible" if title == "Workorder" else "ui-table-cell-hidden"}"><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}"></td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}">{f"Total: ${self.get_total_nest_parts_price(nest_name=nest):,.2f}"}</td></tr>\n'

                html_text += '</tbody></table>'
        else:
            has_items: bool = False
            for i, (item, item_data) in enumerate(self.quote_data.items()):
                if item[0] != '_' and item != "Components":
                    if i == 0:
                        html_text += '''<table id="data-table" data-role="table" data-mode="columntoggle" class="ui-responsive" style="border-collapse: collapse; text-align: center; vertical-align: middle;"><thead><tr class="header-table-row"><th data-priority="1" class="ui-table-cell-visible">Picture</th><th data-priority="2" class="ui-table-cell-visible">Part Name</th><th data-priority="7" class="''' + ("ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible") + '''">Shelf Number</th><th data-priority="6" class="ui-table-cell-visible">Material</th><th data-priority="5" class="ui-table-cell-visible">Thickness</th><th data-priority="4" class="ui-table-cell-visible">Quantity</th><th data-priority="10" class="''' + ("ui-table-cell-visible" if title == "Workorder" else "ui-table-cell-hidden") + '''">Notes</th><th data-priority="9" class="''' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + '''">Unit Price</th><th data-priority="3" class="''' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + '''">Price</th></tr></thead><tbody id="table-body">'''
                        has_items = True
                    html_item_data = '<table class="dltrc" style="background:none;"><tbody><tr class="dlheader" style="height: 20px;"><td class="dlheader">Key</td><td class="dlheader">Value</td></tr>'
                    for data in item_data:
                        html_item_data += f'<tr class="dlinfo hover01" style="height: 20px;"><td class="dlinfo hover01">{data.replace("_", " ").title()}</td><td class="dlinfo hover01"> {item_data[data]}</td></tr>'
                    else:
                        html_item_data += '</tbody></table>'
                    try:
                        shelf_number = item_data["shelf_number"]
                    except KeyError:
                        shelf_number = ""
                    try:
                        flow_tag = " -> ".join(item_data["flow_tag"])
                    except KeyError:
                        flow_tag = ""
                    try:
                        notes = f"{flow_tag}<br>{item_data['notes']}"
                    except KeyError:
                        notes = f"{flow_tag}"
                    try:
                        html_text += f'<tr><td class="ui-table-cell-visible"><div class="image-container"><a class="popup-trigger" href="#{item}" onclick="highlightImage(\'{item}\', \'images/{item}.jpeg\')"><img src="{self.program_directory}/images/{item}.jpeg" style="height: 60px; width: 60px;" alt="Image" id="images/{item}.jpeg"></a><div class="popup" id="{item}"><div class="input-container-horizontal" style="padding: 5px; align-items: left; display: flex;"><img src="{self.program_directory}/images/{item}.jpeg" style="height: 100px; width: 100px;" alt="Image"><h1 style="margin-left: 20px;">{item}</h1></div>{html_item_data}<a class="close-popup" href="#" onclick="clearImageBorders()">Close</a></div></div></td><td class="ui-table-cell-visible">{item}</td><td class="{"ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible"}">{shelf_number}</td><td class="ui-table-cell-visible">{item_data["material"]}</td><td class="ui-table-cell-visible">{item_data["gauge"]}</td><td class="ui-table-cell-visible">{item_data["quantity"]}</td><td class="{"ui-table-cell-visible" if title == "Workorder" else "ui-table-cell-hidden"}">{notes}</td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}">{item_data["unit_price"]}</td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}">{item_data["price"]}</td></tr>\n'
                    except KeyError as e:
                        print(f"Key Error for {e}")
                        continue
            else:
                if has_items:
                    html_text += f'<tr style="height: 20px;"><td class="ui-table-cell-visible"></td><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible"}"></td><td class="ui-table-cell-visible"></td><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-visible" if title == "Workorder" else "ui-table-cell-hidden"}"><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}"></td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}">{f"Total: ${self.get_total_parts_price():,.2f}"}</td></tr>\n'

            html_text += '</tbody></table>'

        if self.quote_data['Components']:
            html_text += f'''<h2 id="components-heading" style="margin-top: 150px; margin-bottom: 0px; text-align: center;"></h2><table id="data-table2" data-role="table" data-mode="columntoggle" class="ui-responsive" style="border-collapse: collapse; text-align: center; vertical-align: middle;"><thead><tr class="header-table-row"><th data-priority="1" class="ui-table-cell-visible">Picture</th><th data-priority="2" class="ui-table-cell-visible">Item Name</th><th data-priority="3" class="ui-table-cell-visible">Item Number</th><th data-priority="8" class="ui-table-cell-visible">Description</th><th data-priority="4" class="''' + ("ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible") + '''">Shelf Number</th><th data-priority="5" class="ui-table-cell-visible">Quantity</th><th data-priority="6" class="''' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + '''">Unit Price</th><th data-priority="7" class="''' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + '''">Price</th></tr></thead><tbody>'''

            for item, item_data in self.quote_data['Components'].items():
                try:
                    shelf_number = item_data["shelf_number"]
                except KeyError:
                    shelf_number = ""
                html_text += f'<tr><td class="ui-table-cell-visible"><img src="{self.program_directory}/{item_data["image_path"]}" style="height: 60px; width: 60px;" alt="Image" id="/{item_data["image_path"]}"></td><td class="ui-table-cell-visible">{item}</td><td class="ui-table-cell-visible">{item_data["part_number"]}</td><td class="ui-table-cell-visible">{item_data["description"]}</td><td class="{"ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible"}">{shelf_number}</td><td class="ui-table-cell-visible">{item_data["quantity"]}</td><td class="' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + f'">${item_data["unit_price"]:,.2f}</td><td class="' + ("ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden") + f'">${item_data["quoting_price"]:,.2f}</td></tr>'
            else:
                html_text += f'<tr style="height: 20px;"><td class="ui-table-cell-visible"></td><td class="ui-table-cell-visible"></td><td class="ui-table-cell-visible"></td><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-hidden" if title != "Workorder" else "ui-table-cell-visible"}"></td><td class="ui-table-cell-visible"></td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}"></td><td class="{"ui-table-cell-visible" if title == "Quote" else "ui-table-cell-hidden"}">{f"Total: ${self.get_total_components_price():,.2f}"}</td></tr>\n'
            html_text += '</tbody></table>'
        html_text += html_end

        if title == 'Workorder':
            with open(f"{self.path_to_save_workorders}/{self.file_name}.html", 'w') as f:
                f.write(BeautifulSoup(html_text, 'html.parser').prettify())
        else:
            with open(f"{self.path_to_save_quotes}/{self.file_name}.html", 'w') as f:
                f.write(BeautifulSoup(html_text, 'html.parser').prettify())

    def generate_quote(self):
        """
        This function generates a quote by creating an Excel file with the given file name and path and
        then calling the generate_excel method on it.
        """
        excel_document = ExcelFile(
            file_name=f"{self.path_to_save_quotes}/{self.file_name}.xlsx",
            generate_quote=True,
            should_generate_packing_slip=False,
            should_generate_workorder=False,
        )
        self.generate_excel(excel_document)

    def generate_packingslip(self):
        """
        This function generates a packingslip by creating an Excel file with the given file name and path and
        then calling the generate_excel method on it.
        """
        excel_document = ExcelFile(
            file_name=f"{self.path_to_save_quotes}/{self.file_name}.xlsx",
            generate_quote=False,
            should_generate_packing_slip=True,
            should_generate_workorder=False,
        )
        self.generate_excel(excel_document)

    def generate_workorder(self):
        """
        This function generates a work order using an Excel file and saves it to a specified path.
        """
        excel_document = ExcelFile(
            file_name=f"{self.path_to_save_workorders}/{self.file_name}.xlsx",
            generate_quote=False,
            should_generate_packing_slip=self.should_generate_packing_slip,
            should_generate_workorder=True,
        )
        self.generate_excel(excel_document)

    def generate_excel(self, excel_document: ExcelFile):
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

        if self.should_generate_quote or self.should_generate_packing_slip:
            headers = [
                "Item",
                "Part name",
                "Material",
                "Thickness",
                "Qty",
                "Unit Price",
                "Price",
            ]
        else:
            headers = [
                "Item",
                "Part name",
                "Material",
                "Thickness",
                "Qty",
            ]

        excel_document.set_cell_width(cell="A1", width=15)
        excel_document.set_cell_width(cell="B1", width=22)
        excel_document.set_cell_width(cell="C1", width=13)
        excel_document.set_cell_width(cell="D1", width=12)
        excel_document.set_cell_width(cell="E1", width=10)
        excel_document.set_cell_width(cell="F1", width=12)
        excel_document.set_cell_width(cell="G1", width=12)

        if self.should_generate_packing_slip:
            excel_document.add_item("F2", f"{self.order_number:05}")

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

            if self.should_generate_quote or self.should_generate_packing_slip:
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
        if self.should_generate_quote or self.should_generate_packing_slip:
            excel_document.add_table(
                display_name="Table1",
                theme="TableStyleLight8",
                location=f"A{STARTING_ROW-1}:G{index+STARTING_ROW-nest_count_index}",
                headers=headers,
            )
        if self.should_generate_workorder:
            excel_document.add_table(
                display_name="Table1",
                theme="TableStyleLight8",
                location=f"A{STARTING_ROW-1}:E{index+STARTING_ROW-nest_count_index}",
                headers=headers,
            )
        index -= nest_count_index + 1
        excel_document.add_item(cell=f"A{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"B{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"C{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"D{index+STARTING_ROW+1}", item="", totals=True)
        excel_document.add_item(cell=f"E{index+STARTING_ROW+1}", item="", totals=True)
        if self.should_generate_quote or self.should_generate_packing_slip:
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

        excel_document.set_print_area(cell=f"A1:G{index + STARTING_ROW+6}")

        # excel_document.add_macro(macro_path=f"{self.program_directory}/macro.bin")
        """
        Macro Code:
        Private Sub Workbook_Open()
            Application.Iteration = True
            Application.MaxIterations = 1
        End Sub
        """

        if self.should_generate_workorder:
            # excel_document.set_col_hidden("F1", True)
            # excel_document.set_col_hidden("G1", True)
            excel_document.freeze_pane(STARTING_ROW)
        else:
            excel_document.freeze_pane(5)
        excel_document.save()

    def get_nests(self) -> list[str]:
        return [item for item in list(self.quote_data.keys()) if item[0] == "_"]

    def get_items(self) -> list[str]:
        if self.should_group_items:
            items = []
            for nest in list(self.quote_data.keys()):
                if nest[0] == '_' or nest == 'Components':
                    continue
                items.extend(list(self.quote_data[nest].keys()))
            return items
        else:
            return [item for item in list(self.quote_data.keys()) if item[0] != "_" and item != "Components"]

    def get_total_sheet_count(self) -> int:
        """
        This function returns the total sheet count by summing the quantity multiplier of each nest in
        the quote data.

        Returns:
          The function `get_total_sheet_count` is returning an integer value which is the sum of the
        `quantity_multiplier` values for all the nests in the `quote_data` dictionary.
        """
        return sum(self.quote_data[nest]["quantity_multiplier"] for nest in self.get_nests())

    def get_total_parts_price(self) -> float:
        if self.should_group_items:
            total = 0.0
            for nest in list(self.quote_data.keys()):
                if nest[0] == '_' or nest == 'Components':
                    continue
                for item in list(self.quote_data[nest].keys()):
                    total += self.quote_data[nest][item]['quoting_price']
            return total
        else:
            return sum(self.quote_data[nest]["quoting_price"] for nest in self.get_items())

    def get_total_nest_parts_price(self, nest_name: str) -> float:
        total = 0.0
        for item in list(self.quote_data[nest_name].keys()):
            total += self.quote_data[nest_name][item]['quoting_price']
        return total

    def get_total_components_price(self) -> float:
        return sum(self.quote_data["Components"][item]["quoting_price"] for item in list(self.quote_data['Components'].keys()))

    def get_total_price(self) -> float:
        return self.get_total_parts_price() + self.get_total_components_price()

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
