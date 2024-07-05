import os
import string
import sys
from datetime import datetime
from typing import Literal

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.assembly import Assembly
from utils.workspace.group import Group
from utils.workspace.job import Job


class CoverPage:
    def __init__(self, job: Job) -> None:
        self.job = job
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def generate(self) -> str:
        return f"""<div id="cover-page">
                <div class="field label prefix border max">
                    <i>numbers</i>
                    <input type="number" id="order-number" value={self.job.order_number}>
                    <label>Order Number</label>
                </div>

                <div class="row">
                    <article class="border max">
                        <div class="field label prefix border">
                            <i>today</i>
                            <input type="date" value="{self.job.date_shipped}">
                            <label>Date Shipped</label>
                        </div>
                        <div class="field label prefix border">
                            <i>today</i>
                            <input type="date" value="{self.job.date_expected}">
                            <label>Date Expected</label>
                        </div>
                    </article>
                    <article class="border max">
                        <div class="field textarea label border">
                            <textarea>{self.job.ship_to}</textarea>
                            <label>Ship To</label>
                        </div>
                        <div class="field border">
                            <input type="text">
                            <span class="helper">Received in good order by</span>
                        </div>
                    </article>
                </div>
            </div>
        </div><br>"""


class NestsTable:
    def __init__(self, job: Job) -> None:
        self.headers = [
            "Nest Name",
            "Thickness",
            "Material",
            "Qty",
            "Sheet Cut Time",
            "Nest Cut Time",
        ]
        self.job = job
        self.grand_total_cut_time = 0.0

    def get_hours_minutes_seconds(self, total_seconds: float) -> tuple[int, int, int]:
        return (
            int(total_seconds // 3600),
            int((total_seconds % 3600) // 60),
            int(total_seconds % 60),
        )

    def get_total_sheet_count(self) -> int:
        return sum(nest.sheet_count for nest in self.job.nests)

    def generate(self) -> str:
        sheets_table_html = """<div id="nests-layout">
                <h5 class="center-align">Nests:</h5>
                <article class="sheets-table border">"""
        sheets_table_html += '<table class="small-text no-space border dynamic-table">'
        sheets_table_html += "<thead><tr>"
        for i, header in enumerate(self.headers):
            sheets_table_html += f'<th data-column="{i}"><label class="checkbox"><input type="checkbox" class="column-toggle" data-column="{i}" checked><span></span></label>{header}</th>'
        sheets_table_html += "</tr></thead>"
        sheets_table_html += '<tbody id="table-body">'
        for nest in self.job.nests:
            single_hours, single_minutes, single_seconds = self.get_hours_minutes_seconds(nest.sheet_cut_time)
            nest_hours, nest_minutes, nest_seconds = self.get_hours_minutes_seconds(nest.get_machining_time())
            self.grand_total_cut_time += nest.get_machining_time()
            sheets_table_html += f"""<tr>
            <td class="small-text" data-column="0">{nest.name}</td>
            <td class="small-text" data-column="1">{nest.sheet.thickness}</td>
            <td class="small-text" data-column="2">{nest.sheet.material}</td>
            <td class="small-text" data-column="3">{nest.sheet_count}</td>
            <td class="small-text" data-column="4">{single_hours:02d}h {single_minutes:02d}m {single_seconds:02d}s</td>
            <td class="small-text" data-column="5">{nest_hours:02d}h {nest_minutes:02d}m {nest_seconds:02d}s</td>
            </tr>"""

        grand_total_hours, grand_total_minutes, grand_total_seconds = self.get_hours_minutes_seconds(self.grand_total_cut_time)
        sheets_table_html += f"""<tr>
        <td class="small-text" data-column="0"></td>
        <td class="small-text" data-column="1"></td>
        <td class="small-text" data-column="2"></td>
        <td class="small-text" data-column="5">{self.get_total_sheet_count()}</td>
        <td class="small-text" data-column="6"></td>
        <td class="small-text" data-column="7">{grand_total_hours:02d}h {grand_total_minutes:02d}m {grand_total_seconds:02d}s</td>
        </tr></tbody></table></article></div><br>"""
        return sheets_table_html


class SheetImages:
    def __init__(self, job: Job):
        self.job = job
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.laser_cut_parts: list[LaserCutPart] = []
        for nest in self.job.nests:
            self.laser_cut_parts.extend(nest.laser_cut_parts)

    def format_filename(self, s: str):
        # https://gist.github.com/seanh/93666
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = "".join(c for c in s if c in valid_chars)
        filename = filename.replace(" ", "_")  # I don't like spaces in filenames.
        return filename

    def get_hours_minutes_seconds(self, total_seconds: float) -> tuple[int, int, int]:
        return (
            int(total_seconds // 3600),
            int((total_seconds % 3600) // 60),
            int(total_seconds % 60),
        )

    def generate_laser_cut_part_data(self, laser_cut_part: LaserCutPart) -> str:
        html = """<table class="no-space border"><tbody>
                <tr>
                   <td class="small-text bold">Key</td>
                   <td class="small-text">Value</td>
                </tr>"""
        for key, value in laser_cut_part.to_dict().items():
            html += f"""<tr>
                <td class="small-text bold">{key.replace("_", " ").title()}</td>
                <td class="small-text">{value}</td>
                </tr>"""
        html += "</tbody></table><br>"
        return html

    def generate_laser_cut_part_popups(self):
        return "".join(
            f"""
            <div class="overlay blur"></div>
            <dialog style="width: 30vw;" class="right" id="NEST-{self.format_filename(laser_cut_part.name)}">
                <img src="{self.server_directory}/{laser_cut_part.image_index}" style="height: 100px; width: 100px;" >
                <h5>{laser_cut_part.name}</h5>
                <div>{self.generate_laser_cut_part_data(laser_cut_part)}</div>
                <nav class="right-align no-space">
                    <button data-ui="#NEST-{self.format_filename(laser_cut_part.name)}" class="transparent link">Close</button>
                </nav>
            </dialog>"""
            for laser_cut_part in self.laser_cut_parts
        )

    def generate(self) -> str:
        html = """<div id="sheets-layout">
                <h5 class="center-align">Sheets:</h5>
                <article class="border"><div class="grid">"""
        for i, nest in enumerate(self.job.nests):
            single_hours, single_minutes, single_seconds = self.get_hours_minutes_seconds(nest.sheet_cut_time)
            nest_hours, nest_minutes, nest_seconds = self.get_hours_minutes_seconds(nest.get_machining_time())
            if nest.sheet_count == 1:
                cut_time = f'<div class="small-text">Cut Time: {nest_hours:02d}h {nest_minutes:02d}m {nest_seconds:02d}s</div>'
            else:
                cut_time = f"""<div class="small-text">Sheet Cut Time: {single_hours:02d}h {single_minutes:02d}m {single_seconds:02d}s</div>
                            <div class="small-text">Nest Cut Time: {nest_hours:02d}h {nest_minutes:02d}m {nest_seconds:02d}s</div>"""
            parts_list = '<article class="no-padding" style="width: 300px;">'
            for part in nest.laser_cut_parts:
                parts_list += f'''
                <a class="row padding surface-container wave" onclick="ui('#NEST-{self.format_filename(part.name)}');">
                    <img class="round" src="{self.server_directory}/{part.image_index}">
                    <div class="max">
                        <h6 class="small">{part.name}</h6>
                        <div>Quantity: {part.quantity_in_nest}</div>
                    </div>
                    <div class="badge none">#{part.part_number}</div>
                </a>
                <div class="divider"></div>'''
            parts_list += '</article>'
            html += f"""
            <div class="s6">
                <article class="nest no-padding border">
                    <img style="margin-bottom: -50px; margin-top: -40px; z-index: -1; height: auto;" src="{self.server_directory}/image/{nest.image_path}" class="responsive small nest_image">
                    <div class="{'right-align' if i % 2 == 0 else 'left-align'}">
                        <button class="nested-parts transparent small small-round">
                            <i>format_list_bulleted</i>
                            <span>Parts</span>
                            <div class="tooltip {'right' if i % 2 == 0 else 'left'}">
                                {parts_list}
                            </div>
                        </button>
                    </div>
                    <div class="small-padding">
                        <div class="row">
                            <h5 class="small max">{nest.name}</h5>
                            <div class="badge none">{int(nest.sheet_count)}</div>
                        </div>
                        <div class="row surface-container">
                            <div class="max">
                                <div class="small-text">
                                    <button class="transparent square small">
                                        <i>qr_code_2</i>
                                        <div class="tooltip right">
                                            <div class="qr-item" data-name="{nest.sheet.get_name()}">
                                                <div class="qr-code"></div>
                                            </div>
                                        </div>
                                    </button>
                                    {nest.sheet.thickness} {nest.sheet.material} {nest.sheet.get_sheet_dimension()}
                                </div>
                                {cut_time}
                            </div>
                        </div>
                    </div>
                </article>
            </div>"""
        html += "</article></div></div><br>"
        return html


class LaserCutPartsTable:
    def __init__(self, assembly_quantity: int, laser_cut_parts: list[LaserCutPart]) -> None:
        self.headers = [
            "Part",
            "Material",
            "Thickness",
            "Unit Qty",
            "Qty",
            "Process",
            "Shelf #",
            "Unit Price",
            "Price",
        ]
        self.assembly_quantity = assembly_quantity
        self.laser_cut_parts = laser_cut_parts
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def format_filename(self, s: str):
        # https://gist.github.com/seanh/93666
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = "".join(c for c in s if c in valid_chars)
        filename = filename.replace(" ", "_")  # I don't like spaces in filenames.
        return filename

    def generate_laser_cut_part_data(self, laser_cut_part: LaserCutPart) -> str:
        html = """<table class="no-space border"><tbody>
                <tr>
                   <td class="small-text bold">Key</td>
                   <td class="small-text">Value</td>
                </tr>"""
        for key, value in laser_cut_part.to_dict().items():
            html += f"""<tr>
                <td class="small-text bold">{key.replace("_", " ").title()}</td>
                <td class="small-text">{value}</td>
                </tr>"""
        html += "</tbody></table><br>"
        return html

    def generate_laser_cut_part_popups(self):
        return "".join(
            f"""
            <div class="overlay blur"></div>
            <dialog style="width: 30vw;" class="right" id="LCP-{self.format_filename(laser_cut_part.name)}">
                <img src="{self.server_directory}/{laser_cut_part.image_index}" style="height: 100px; width: 100px;" >
                <h5>{laser_cut_part.name}</h5>
                <div>{self.generate_laser_cut_part_data(laser_cut_part)}</div>
                <nav class="right-align no-space">
                    <button data-ui="#LCP-{self.format_filename(laser_cut_part.name)}" class="transparent link">Close</button>
                </nav>
            </dialog>"""
            for laser_cut_part in self.laser_cut_parts
        )

    def get_total_cost(self) -> float:
        total = 0.0
        for laser_cut_part in self.laser_cut_parts:
            total += round(laser_cut_part.price, 2) * laser_cut_part.quantity
        return total

    def generate(self) -> str:
        html = '<table class="no-space border dynamic-table">'
        html += "<thead><tr>"
        for i, header in enumerate(self.headers):
            html += f'<th class="small-text" data-column="{i}"><label class="checkbox"><input type="checkbox" class="column-toggle" data-column="{i}" data-name="{header.lower().replace(" ", "-")}" checked><span></span></label>{header}</th>'
        html += "</tr>"
        html += "</thead>"
        html += "<tbody>"
        for laser_cut_part in self.laser_cut_parts:
            html += f'''<tr>
            <td class="min" data-column="0" data-name="part">
                <button class="extra transparent small-round" onclick="ui('#LCP-{self.format_filename(laser_cut_part.name)}');">
                <img class="responsive" src="{self.server_directory}/{laser_cut_part.image_index}">
                <span class="small-text">{laser_cut_part.name}</span>
            </td>
            <td class="small-text" data-column="1" data-name="material">{laser_cut_part.material}</td>
            <td class="small-text" data-column="2" data-name="thickness">{laser_cut_part.gauge}</td>
            <td class="small-text" data-column="3" data-name="unit-qty">{laser_cut_part.quantity}</td>
            <td class="small-text" data-column="4" data-name="qty">{laser_cut_part.quantity * self.assembly_quantity}</td>
            <td class="small-text min" data-column="5" data-name="process">{laser_cut_part.flow_tag.get_name()}</td>
            <td class="small-text" data-column="6" data-name="shelf-#">{laser_cut_part.shelf_number}</td>
            <td class="small-text" data-column="7" data-name="unit-price">${laser_cut_part.price:,.2f}</td>
            <td class="small-text" data-column="8" data-name="price">${(laser_cut_part.price * laser_cut_part.quantity):,.2f}</td>
            </tr>'''
        html += f'''<tr>
                <th class="small-text" data-column="0" data-name="part"></th>
                <th class="small-text" data-column="1" data-name="material"></th>
                <th class="small-text" data-column="2" data-name="thickness"></th>
                <th class="small-text" data-column="3" data-name="unit-qty"></th>
                <th class="small-text" data-column="4" data-name="qty"></th>
                <th class="small-text" data-column="5" data-name="process"></th>
                <th class="small-text" data-column="6" data-name="shelf-#"></th>
                <th class="small-text" data-column="7" data-name="unit-price"></th>
                <th class="small-text" data-column="8" data-name="price">Total: ${self.get_total_cost():,.2f}</th>
            </tr></tbody></table>'''
        return html


class ComponentsTable:
    def __init__(self, assembly_quantity: int, components: list[Component]) -> None:
        self.assembly_quantity = assembly_quantity
        self.components = components
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.headers = ["Part", "Part #", "Shelf #", "Unit Qty", "Qty", "Unit Price", "Price"]

    def format_filename(self, s):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = "".join(c for c in s if c in valid_chars)
        filename = filename.replace(" ", "_")  # I don't like spaces in filenames.
        return filename

    def generate_components_data(self, laser_cut_part: LaserCutPart) -> str:
        html = """<table class="no-space border"><tbody>
                <tr>
                   <td class="small-text bold">Key</td>
                   <td class="small-text">Value</td>
                </tr>"""
        for key, value in laser_cut_part.to_dict().items():
            html += f"""<tr>
                <td class="small-text bold">{key.replace("_", " ").title()}</td>
                <td class="small-text">{value}</td>
                </tr>"""
        html += "</tbody></table><br>"
        return html

    def generate_components_popups(self):
        return "".join(
            f"""
            <div class="overlay blur"></div>
            <dialog style="width: 30vw;" class="right" id="C-{self.format_filename(component.part_name)}">
                <img src="{self.server_directory}/{component.image_path}" style="height: 100px; width: 100px;" >
                <h5>{component.part_name}</h5>
                <div>{self.generate_components_data(component)}</div>
                <nav class="right-align no-space">
                    <button data-ui="#C-{self.format_filename(component.part_name)}" class="transparent link">Close</button>
                </nav>
            </dialog>"""
            for component in self.components
        )

    def get_total_cost(self) -> float:
        total = 0.0
        for component in self.components:
            total += round(component.price, 2) * component.quantity
        return total

    def generate(self):
        html = '<table class="no-space border">'
        html += "<thead><tr>"
        for i, header in enumerate(self.headers):
            html += f'<th class="small-text" data-column="{i}"><label class="checkbox"><input type="checkbox" class="column-toggle" data-column="{i}" data-name="{header.lower().replace(" ", "-")}" checked><span></span></label>{header}</th>'
        html += "</tr></thead><tbody>"
        for component in self.components:
            html += f"""<tr>
            <td class="min" data-column="0" data-name="part">
                <button class="extra transparent small-round" onclick="ui('#C-{self.format_filename(component.part_name)}');">
                <img class="responsive" src="{self.server_directory}/{component.image_path}">
                <span class="small-text">{component.part_name}</span>
            </td>
            <td class="small-text" data-column="1" data-name="part-#">{component.part_number}</td>
            <td class="small-text" data-column="2" data-name="shelf-#">{component.shelf_number}</td>
            <td class="small-text" data-column="3" data-name="unit-qty">{component.quantity}</td>
            <td class="small-text" data-column="4" data-name="qty">{component.quantity * self.assembly_quantity}</td>
            <td class="small-text" data-column="5" data-name="unit-price">${component.price:,.2f}</td>
            <td class="small-text" data-column="6" data-name="price">${(component.price * component.quantity):,.2f}</td>
            </tr>"""
        html += f"""</tbody><tfoot><tr>
        <th class="small-text" data-column="0" data-name="picture"></th>
        <th class="small-text" data-column="1" data-name="part-#"></th>
        <th class="small-text" data-column="2" data-name="shelf-#"></th>
        <th class="small-text" data-column="3" data-name="unit-qty"></th>
        <th class="small-text" data-column="4" data-name="qty"></th>
        <th class="small-text" data-column="5" data-name="unit-price"></th>
        <th class="small-text" data-column="6" data-name="price">Total: ${self.get_total_cost():,.2f}</th>
        </tr></tfoot></table>"""
        return html


class AssemblyTable:
    def __init__(self, job: Job):
        self.headers = ["Image", "Assembly Name", "Qty", "Process"]
        self.job = job
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def generate(self) -> str:
        html = """<div id="assemblies-list-layout">
                <h5 class="center-align">Assemblies:</h5>
                <article class="assembly-table border">"""
        for assembly in self.job.get_all_assemblies():
            html += f"""
            <a class="row padding surface-container wave">
                <img src="{self.server_directory}/image/{assembly.assembly_image}" class="assembly_image round">
                <div class="max">
                    <h6 class="small">{assembly.name}</h6>
                    <div>{assembly.flow_tag.get_name()}</div>
                </div>
                <div class="badge none">{int(assembly.quantity)}</div>
            </a><div class="divider"></div>"""
        html += "</article></div><br>"
        return html


class JobDiv:
    def __init__(self, job: Job) -> None:
        self.job = job

    def generate(self) -> str:
        html = ""
        for group in self.job.groups:
            group_div = GroupDiv(group)
            html += group_div.generate()
        return html


class GroupDiv:
    def __init__(self, group: Group) -> None:
        self.group = group

    def generate(self) -> str:
        html = '<details class="group_details" open>'
        html += f"<summary>{self.group.name}</summary>"
        html += '<div class="group">'
        for assembly in self.group.assemblies:
            assembly_div = AssemblyDiv(assembly)
            html += assembly_div.generate()
        html += "</div>"
        html += "</details>"
        return html


class AssemblyDiv:
    def __init__(self, assembly: Assembly, use_recursion=True) -> None:
        self.assembly = assembly
        self.use_recursion = use_recursion
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def get_assembly_data_html(self) -> str:
        html = '<div class="assembly_data">'
        image_html = f'<img src="{self.server_directory}/image/{self.assembly.assembly_image}" class="assembly_image">' if self.assembly.assembly_image else ""
        html += image_html
        html += '<div class="padding">'
        html += f'<h5>{self.assembly.name} <div class="badge none">{int(self.assembly.quantity)}</div></h5>'
        html += f'<p class="small-text">Process: {self.assembly.flow_tag.get_name()}</p>'
        html += "</div>"
        html += "</div>"
        return html

    def generate(self) -> str:
        html = '<details class="assembly_details" open>'
        html += f'<summary>{self.assembly.name} × {int(self.assembly.quantity)}</summary>'
        html += '<div class="assembly">'
        html += self.get_assembly_data_html()

        if self.assembly.laser_cut_parts:
            html += '<details class="laser_cut_parts_detail" open>'
            html += "<summary>Laser Cut Parts</summary>"
            html += '<div class="detail_contents laser_cut_part_contents">'
            laser_cut_table = LaserCutPartsTable(self.assembly.quantity, self.assembly.laser_cut_parts)
            html += laser_cut_table.generate()
            html += "</div>"
            html += "</details>"

        if self.assembly.components:
            html += '<details class="components_detail" open>'
            html += "<summary>Components</summary>"
            html += '<div class="detail_contents components_contents">'
            component_table = ComponentsTable(self.assembly.quantity, self.assembly.components)
            html += component_table.generate()
            html += "</div>"
            html += "</details>"

        # if self.assembly.laser_cut_parts or self.assembly.components:
        #     html += '<div id="page-break" class="page-break"></div>'

        if self.assembly.sub_assemblies and self.use_recursion:
            html += "<details open>"
            html += "<summary>Sub-Assemblies</summary>"
            html += '<div class="detail_contents assembly">'
            for sub_assembly in self.assembly.sub_assemblies:
                sub_assembly_div = AssemblyDiv(sub_assembly)
                html += sub_assembly_div.generate()
            html += "</div>"
            html += "</details>"

        html += "</div>"
        html += "</details>"
        return html


class PrintoutHeader:
    def __init__(
        self,
        job: Job,
        printout_type: Literal["QUOTE", "WORKORDER", "PACKINGSLIP"] = "QUOTE"
    ) -> None:
        self.job = job
        self.printout_type = printout_type
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.html = f'''<header>
            <nav>
                <img class="logo" src="{self.server_directory}/images/logo.png">
                <h5 class="max center-align small">
                    {self.job.name}
                </h5>
                <div class="date">
                    {str(datetime.now().strftime("%I:%M:%S %p %A %B %d, %Y"))}
                </div>
            </nav>
            <nav class="tabbed primary-container">
                <a {'class="active primary"' if self.printout_type == "QUOTE" else ''} data-target="quote">
                    <i>request_quote</i>
                    <span>Quote</span>
                </a>
                <a {'class="active primary"' if self.printout_type == "WORKORDER" else ''} data-target="workorder">
                    <i>manufacturing</i>
                    <span>Workorder</span>
                </a>
                <a {'class="active primary"' if self.printout_type == "PACKINGSLIP" else ''} data-target="packingslip">
                    <i>receipt_long</i>
                    <span>Packing Slip</span>
                </a>
            </nav>
        </header>'''


class Printout:
    def __init__(
        self,
        job: Job,
        printout_type: Literal["QUOTE", "WORKORDER", "PACKINGSLIP"] = "QUOTE"
    ) -> None:
        self.job = job
        self.printout_type = printout_type
        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

        with open("utils/workspace/printout.css", "r", encoding="utf-8") as printout_css_file:
            self.printout_css = printout_css_file.read()

        with open("utils/workspace/printout.js", "r", encoding="utf-8") as printout_js_file:
            self.printout_js = printout_js_file.read()

    def get_total_price(self) -> float:
        total = 0.0
        for component in self.job.get_all_components():
            total += round(component.price, 2) * component.quantity
        for laser_cut_part in self.job.get_all_laser_cut_parts():
            total += round(laser_cut_part.price, 2) * laser_cut_part.quantity
        return total

    def generate(self) -> str:
        header_html = PrintoutHeader(self.job, self.printout_type).html
        html = f"""<!DOCTYPE html>
                <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <meta http-equiv="X-UA-Compatible" content="ie=edge">
                        <meta name="google" content="notranslate">
                        <script src="https://cdn.jsdelivr.net/gh/davidshimjs/qrcodejs/qrcode.min.js"></script>
                        <link href="https://cdn.jsdelivr.net/npm/beercss@3.6.0/dist/cdn/beer.min.css" rel="stylesheet">
                        <script type="module" src="https://cdn.jsdelivr.net/npm/beercss@3.6.0/dist/cdn/beer.min.js"></script>
                        <script src="https://code.jquery.com/jquery-3.7.1.min.js" integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo=" crossorigin="anonymous"></script>
                        <script type="module" src="https://cdn.jsdelivr.net/npm/material-dynamic-colors@1.1.2/dist/cdn/material-dynamic-colors.min.js"></script>
                        <link rel="stylesheet" type="text/css" href="/static/theme.css">
                        <title>{self.printout_type.title()} {self.job.name}</title>
                        <meta property="og:title" content="{self.printout_type.title()} - {self.job.name}" />
                        <meta property="og:description" content="{self.job.ship_to}" />
                    </head>
        <style>
            {self.printout_css}
        </style>
        <body class="quote">
        <main class="responsive">
        {header_html}
        <div class="center-align" id="printout-controls">
            <label class="checkbox">
                <input type="checkbox" id="showCoverPage" data-name="show-cover-page" data-layout="cover-page" checked>
                <span>Show Cover Page</span>
            </label>
            <br>
            <label class="checkbox">
                <input type="checkbox" id="showAssemblies" data-name="show-assemblies" data-layout="assemblies-list-layout" {"checked" if self.job.groups else ""}>
                <span>Show Assemblies</span>
            </label>
            <br>
            <label class="checkbox">
                <input type="checkbox" id="showNests" data-name="show-nests" data-layout="nests-layout" {"checked" if self.job.nests else ""}>
                <span>Show Nests</span>
            </label>
            <br>
            <label class="checkbox">
                <input type="checkbox" id="showSheets" data-name="show-sheets" data-layout="sheets-layout" {"checked" if self.job.nests else ""}>
                <span>Show Sheets</span>
            </label>
            <br>
            <label class="checkbox">
                <input type="checkbox" id="showParts" data-name="show-parts" data-layout="parts-layout" {"checked" if self.job.get_all_components() or self.job.get_all_laser_cut_parts() else ""}>
                <span>Show Parts</span>
            </label>
            <br>
            <label class="checkbox">
                <input type="checkbox" id="showTotalCost" data-name="show-total-cost" data-layout="total-cost-layout" checked>
                <span>Show Total Cost</span>
            </label>
            <br>
            <label class="checkbox">
                <input type="checkbox" id="usePageBreaks" data-name="use-page-breaks" data-layout="page-break" checked>
                <span>Use Page Breaks</span>
            </label>
        </div>
        <br>"""

        cover_page = CoverPage(self.job)

        html += cover_page.generate()

        all_assemblies = self.job.get_all_assemblies()

        if all_assemblies:
            assembly_table = AssemblyTable(self.job)
            html += assembly_table.generate()

        if self.job.nests:
            sheets_table = NestsTable(self.job)
            html += sheets_table.generate()

            nests_table = SheetImages(self.job)
            html += nests_table.generate()

        html += '<div id="parts-layout"><div id="page-break" class="page-break"></div>'
        html += """<div class="tabs">
            <a class="active" data-ui="#assemblies-layout"><i>table_view</i>Assemblies Layout</a>
            <a data-ui="#assemblies-list"> <i>data_table</i>Assemblies List</a>
            <a data-ui="#parts-list"> <i>format_list_bulleted</i>Grouped Parts List</a>
        </div>"""
        html += '<div class="page right active" id="assemblies-layout">'
        if self.job.groups:
            job_div = JobDiv(self.job)
            html += job_div.generate()
        else:
            html += "Nothing here"
        html += "</div>"

        html += '<div class="page" id="assemblies-list" class="hidden">'
        if all_assemblies:
            for assembly in all_assemblies:
                assembly_div = AssemblyDiv(assembly, False)
                html += assembly_div.generate()
                html += '<div id="page-break" class="page-break"></div>'
        else:
            html += "Nothing here"
        html += "</div>"

        grouped_laser_cut_parts = self.job.get_grouped_laser_cut_parts()
        grouped_components = self.job.get_grouped_components()

        html += '<div class="page left" id="parts-list" class="hidden">'
        if grouped_laser_cut_parts and grouped_components:
            if grouped_laser_cut_parts:
                html += '<h5 class="center-align">Laser Cut Parts:</h5>'
                grouped_laser_cut_parts_table = LaserCutPartsTable(1, grouped_laser_cut_parts)
                html += grouped_laser_cut_parts_table.generate()
            if grouped_components:
                html += '<h5 class="center-align">Components:</h5>'
                grouped_components_table = ComponentsTable(1, grouped_components)
                html += grouped_components_table.generate()
        else:
            html += "Nothing here"
        html += "</div>"
        html += "</div>" # for the tabs

        if grouped_components or grouped_laser_cut_parts:
            html += f"""
            <div id="total-cost-layout">
                <h6 class="center-align bold">Total Cost: ${self.get_total_price():,.2f}</h6>
                <p class="small-text center-align bold underline">No tax is included in this quote.</p>
                <p class="small-text center-align">Payment past due date will receive 1.5% interest rate per month of received goods.</p>
            </div>"""
        if grouped_laser_cut_parts:
            html += grouped_laser_cut_parts_table.generate_laser_cut_part_popups()
        if grouped_components:
            html += grouped_components_table.generate_components_popups()
        html += nests_table.generate_laser_cut_part_popups()

        html += "</main></body>"
        html += f"""<script>
            {self.printout_js}
            toggleCheckboxes("{self.printout_type.lower()}", navCheckBoxLinks);
        </script>"""
        return html
