import os
import string
import sys
from datetime import datetime
from typing import Literal

from natsort import natsorted

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class Head:
    def __init__(self, title: str, description: str) -> None:
        self.html = f"""
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <meta http-equiv="X-UA-Compatible" content="ie=edge">
                <meta name="google" content="notranslate">
                <title>{title}</title>
                <meta property="og:title" content="{title}" />
                <meta property="og:description" content="{description}" />
                <link href="/dist/css/printout.bundle.css" rel="stylesheet">
                <script src="/dist/js/qrcode.min.js"></script>
                <script type="module" src="/dist/js/printout.bundle.js"></script>
            </head>"""


class CoverPage:
    def __init__(
        self,
        order_number: float,
        PO_number: float,
        date_shipped: str,
        date_expected: str,
        ship_to: str,
    ):
        self.order_number = order_number
        self.PO_number = PO_number
        self.date_shipped = date_shipped
        self.date_expected = date_expected
        self.ship_to = ship_to
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def generate(self) -> str:
        formatted_date_shipped = datetime.strptime(
            self.date_shipped, "%Y-%m-%d %I:%M %p"
        ).strftime("%Y-%m-%dT%H:%M")
        formatted_date_expected = datetime.strptime(
            self.date_expected, "%Y-%m-%d %I:%M %p"
        ).strftime("%Y-%m-%dT%H:%M")

        return f"""<div id="cover-page">
                <div class="grid">
                    <div class="field label prefix border max s2">
                        <i>numbers</i>
                        <input type="number" id="order-number" value={int(self.order_number)}>
                        <label>Order Number</label>
                    </div>
                    <div class="field label prefix border max s2">
                        <i>numbers</i>
                        <input type="number" id="PO-number" value={int(self.PO_number)}>
                        <label>PO Number</label>
                    </div>
                    <div class="field label prefix border s4">
                        <i>today</i>
                        <input type="text">
                        <label>Date Shipped</label>
                    </div>
                    <div class="field label prefix border s4">
                        <i>date_range</i>
                        <input type="datetime-local" value="{formatted_date_expected}">
                        <label>Date Expected</label>
                    </div>
                    <div class="field textarea label border s6">
                        <textarea>{self.ship_to}</textarea>
                        <label>Ship To</label>
                    </div>
                    <div class="field border extra s6">
                        <input type="text">
                        <span class="helper">Received in good order by</span>
                    </div>
                </div>
            </div>
        </div><br>"""


class WorkorderID:
    def __init__(self, workorder_id: str):
        self.workorder_id = workorder_id

    def generate(self) -> str:
        return f"""<div><h5 class="center-align">Scan to Open Workorder</h5><div class='padding' id='workorder-id' data-workorder-id={self.workorder_id}></div></div>"""


class NestRecutPartSummary:
    def __init__(self, nests: list[Nest]):
        self.nests = natsorted(nests, key=lambda nest: nest.name)
        self.headers = ["Nest", "Recut Part Summary"]

    def get_nest_recut_part_summary(self, nest: Nest) -> str:
        summary = "<p class='small-text'>"
        for part in nest.laser_cut_parts:
            if part.recut:
                if part.recut_count_notes == 1:
                    summary += f"<span class='small-text' id='{part.name}-summary'>{part.name} (Part #{part.part_number}) has {part.recut_count_notes} recut</span><br>"
                else:
                    summary += f"<span class='small-text' id='{part.name}-summary'>{part.name} (Part #{part.part_number}) has {part.recut_count_notes} recuts</span><br>"
        summary += "</p>"
        return summary

    def generate(self) -> str:
        html = "<div class='max' id='recut-parts-summary-layout'>"
        html += "<article class='border'>"
        html += "<table class='small-space border responsiveTable'><thead><tr>"
        for i, header in enumerate(self.headers):
            html += f'<th class="small-text" data-column="{i}">{header}</th>'
        html += "</tr></thead><tbody>"
        for nest in self.nests:
            if not nest.notes:
                continue
            html += f"""<tr>
            <td class="min" data-label="{self.headers[0]}" data-column="0" data-name="nest-name">
                <span class="small-text">{nest.get_name()}</span>
            </td>
            <td class="small-text left-align" data-label="{self.headers[1]}" data-column="1" data-name="notes">{self.get_nest_recut_part_summary(nest)}</td>
            </tr>"""
        html += """<tr>
                <th class="small-text" data-label="{self.headers[0]}" data-column="0" data-name="nest-name"></th>
                <th class="small-text max" data-label="{self.headers[1]}" data-column="1" data-name="notes"></th>
            </tr></tbody></table>"""
        html += "</article></div>"
        return html


class NestsTable:
    def __init__(self, nests: list[Nest]):
        self.headers = [
            "Nest Name",
            "Material",
            "Dimensions",
            "Qty",
            "Sheet Cut Time",
            "Nest Cut Time",
        ]
        self.nests = natsorted(nests, key=lambda nest: nest.name)
        self.grand_total_cut_time = 0.0

    def get_formatted_time(self, total_seconds: float) -> tuple[int, int, int]:
        return (
            int(total_seconds // 3600),
            int((total_seconds % 3600) // 60),
            int(total_seconds % 60),
        )

    def get_total_sheet_count(self) -> int:
        return sum(nest.sheet_count for nest in self.nests)

    def generate(self) -> str:
        html = """<div id="nests-layout">
                <h5 class="center-align">Nests:</h5>
                <article class="sheets-table border">"""
        if not self.nests:
            html += "Nothing here"
        else:
            html += '<table class="small-text no-space border dynamic-table responsiveTable">'
            html += "<thead><tr>"
            for i, header in enumerate(self.headers):
                html += f'<th data-column="{i}"><label class="checkbox"><input type="checkbox" class="column-toggle" data-column="{i}" checked><span></span></label>{header}</th>'
            html += "</tr></thead><tbody>"
            for nest in self.nests:
                single_hours, single_minutes, single_seconds = self.get_formatted_time(
                    nest.sheet_cut_time
                )
                nest_hours, nest_minutes, nest_seconds = self.get_formatted_time(
                    nest.get_machining_time()
                )
                self.grand_total_cut_time += nest.get_machining_time()
                html += f"""<tr>
                <td data-label="{self.headers[0]}" data-column="0"><span class="small-text">{nest.name}</span></td>
                <td data-label="{self.headers[1]}" data-column="1"><span class="small-text">{nest.sheet.thickness} {nest.sheet.material}</span></td>
                <td data-label="{self.headers[2]}" data-column="2"><span class="small-text">{nest.sheet.get_sheet_dimension()}</span></td>
                <td data-label="{self.headers[3]}" data-column="3"><span class="small-text">{nest.sheet_count}</span></td>
                <td data-label="{self.headers[4]}" data-column="4"><span class="small-text">{single_hours:02d}h {single_minutes:02d}m {single_seconds:02d}s</span></td>
                <td data-label="{self.headers[5]}" data-column="5"><span class="small-text">{nest_hours:02d}h {nest_minutes:02d}m {nest_seconds:02d}s</span></td>
                </tr>"""
            grand_total_hours, grand_total_minutes, grand_total_seconds = (
                self.get_formatted_time(self.grand_total_cut_time)
            )
            html += f"""<tr>
            <td data-label="" data-column="0"></td>
            <td data-label="" data-column="1"></td>
            <td data-label="" data-column="2"></td>
            <td data-label="{self.headers[3]}" data-column="3"><span class="small-text">{self.get_total_sheet_count()}</span></td>
            <td data-label="" data-column="4"></td>
            <td data-label="{self.headers[5]}" data-column="5"><span class="small-text">{grand_total_hours:02d}h {grand_total_minutes:02d}m {grand_total_seconds:02d}s</span></td>
            </tr>
            </tbody>
            </table>"""
        html += "</article></div><br>"
        return html


class SheetImages:
    def __init__(self, nests: list[Nest]):
        self.nests = nests
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.laser_cut_parts: list[LaserCutPart] = []
        for nest in self.nests:
            self.laser_cut_parts.extend(nest.laser_cut_parts)

    def format_filename(self, s: str):
        # https://gist.github.com/seanh/93666
        valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
        filename = "".join(c for c in s if c in valid_chars)
        return filename.replace(" ", "_")

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
        if not self.nests:
            html += "Nothing here"
        else:
            for i, nest in enumerate(self.nests):
                single_hours, single_minutes, single_seconds = (
                    self.get_hours_minutes_seconds(nest.sheet_cut_time)
                )
                nest_hours, nest_minutes, nest_seconds = self.get_hours_minutes_seconds(
                    nest.get_machining_time()
                )
                if nest.sheet_count == 1:
                    cut_time = f'<div class="small-text">Cut Time: {nest_hours:02d}h {nest_minutes:02d}m {nest_seconds:02d}s</div>'
                else:
                    cut_time = f"""<div class="small-text">Sheet Cut Time: {single_hours:02d}h {single_minutes:02d}m {single_seconds:02d}s</div>
                                <div class="small-text">Nest Cut Time: {nest_hours:02d}h {nest_minutes:02d}m {nest_seconds:02d}s</div>"""
                parts_list = '<article class="no-padding" style="width: 300px;">'
                for part in nest.laser_cut_parts:
                    parts_list += f"""
                    <a class="row padding surface-container wave" onclick="ui('#NEST-{self.format_filename(part.name)}');">
                        <img class="round" src="{self.server_directory}/{part.image_index}">
                        <div class="max">
                            <h6 class="small">{part.name}</h6>
                            <div>Quantity: {part.quantity_on_sheet:,.0f}</div>
                        </div>
                        <div class="badge none">#{part.part_number}</div>
                    </a>
                    <div class="divider"></div>"""
                parts_list += "</article>"
                html += f"""
                <div class="s6" id="nest-container">
                    <article class="nest no-padding border">
                        <img src="{self.server_directory}/image/{nest.image_path}" class="responsive nest_image">
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
                                <h5>× {int(nest.sheet_count)}</h5>
                            </div>
                            <div class="row">
                                <div class="max">
                                    <div class="small-text">
                                        <button class="transparent circle small-round small">
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
        html += '</article></div></div></article><br><div id="page-break" class="page-break"></div>'
        return html


class NestedLaserCutParts:
    def __init__(self, nests: list[Nest]):
        self.nests = nests
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.headers = ["Part", "Part #", "Sheet Qty", "Qty"]

    def format_filename(self, s: str):
        valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
        filename = "".join(c for c in s if c in valid_chars)
        return filename.replace(" ", "_")

    def generate_laser_cut_part_table(self, nest: Nest) -> str:
        html = (
            '<table class="no-space border dynamic-table responsiveTable"><thead><tr>'
        )
        for i, header in enumerate(self.headers):
            html += f'<th class="small-text" data-column="{i}"><label class="checkbox"><input type="checkbox" class="column-toggle" data-column="{i}" data-name="{header.lower().replace(" ", "-")}" checked><span></span></label>{header}</th>'
        html += "</tr>"
        html += "</thead>"
        html += "<tbody>"
        for laser_cut_part in nest.laser_cut_parts:
            recut_part_string = ""
            if laser_cut_part.recut:
                recut_part_string = f"<br><span class='small-text no-line'>(Recuts: {laser_cut_part.recut_count_notes})</span>"
            html += f"""<tr>
            <td class="min" data-label="{self.headers[0]}" data-column="0" data-name="part">
                <button class="extra transparent small-round" onclick="ui('#NEST-{self.format_filename(laser_cut_part.name)}');">
                <img class="responsive" src="{self.server_directory}/{laser_cut_part.image_index}">
                <span class="small-text">{laser_cut_part.name}</span>
                </button>
            </td>
            <td data-label="{self.headers[1]}" data-column="1" data-name="part-#"><i>tag</i><span class="small-text">{laser_cut_part.part_number}</span></td>
            <td data-label="{self.headers[2]}" data-column="2" data-name="sheet-qty"><span class="small-text">{laser_cut_part.quantity_on_sheet:,.0f}</span></td>
            <td data-label="{self.headers[3]}" data-column="3" data-name="qty"><span class="small-text">{laser_cut_part.quantity:,.0f}{recut_part_string}</span></td>
            </tr>"""
        html += """<tr>
            <th class="small-text" data-label="{self.headers[0]}" data-column="0" data-name="part"></th>
            <th class="small-text" data-label="{self.headers[1]}" data-column="1" data-name="part-#"></th>
            <th class="small-text" data-label="{self.headers[2]}" data-column="2" data-name="sheet-qty"></th>
            <th class="small-text" data-label="{self.headers[3]}" data-column="3" data-name="qty"></th>
        </tr></tbody></table>"""
        return html

    def generate(self) -> str:
        html = '<div id="nested-parts-layout"><h5 class="center-align">Nested Laser Cut Parts:</h5>'
        if not self.nests:
            html += '<article class="border nest-summary">Nothing here</article>'
        else:
            for i, nest in enumerate(self.nests):
                html += (
                    '<article class="border nest-summary"><div class="center-align">'
                )
                html += f'<h6 class="center-align">{nest.get_name()}</h6><br>'
                html += f'<img src="{self.server_directory}/image/{nest.image_path}" class="responsive nest_image"></div>'
                html += self.generate_laser_cut_part_table(nest)
                html += "</article>"
                if i < len(self.nests) - 1:  # Check if it's not the last item
                    html += '<div id="page-break" class="page-break"></div>'
        html += "</div>"
        return html


class LaserCutPartsTable:
    def __init__(
        self, job: Job, assembly_quantity: int, laser_cut_parts: list[LaserCutPart]
    ):
        self.job = job
        self.assembly_quantity = assembly_quantity
        self.laser_cut_parts = laser_cut_parts
        self.headers = [
            "Part",
            "Material",
            "Process",
            "Notes",
            "Shelf #",
            "Unit Qty",
            "Qty",
            "Unit Price",
            "Price",
        ]
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def format_filename(self, s: str):
        valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
        filename = "".join(c for c in s if c in valid_chars)
        return filename.replace(" ", "_")

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
            total += (
                self.job.price_calculator.get_laser_cut_part_cost(laser_cut_part)
                * laser_cut_part.quantity
                * self.assembly_quantity
            )
        return total

    def get_paint(self, laser_cut_part: LaserCutPart) -> str:
        html = '<div class="no-padding small-text grid center-align">'
        if laser_cut_part.uses_primer and laser_cut_part.primer_item:
            html += f'<div class="no-margin s12"><div class="tiny-margin" style="height: 20px; width: 20px; display: inline-flex; background-color: {laser_cut_part.primer_item.color}; border-radius: 5px;"></div><span class="tiny-margin">{laser_cut_part.primer_item.name}</span></div>'
        if laser_cut_part.uses_paint and laser_cut_part.paint_item:
            html += f'<div class="no-margin s12"><div class="tiny-margin" style="height: 20px; width: 20px; display: inline-flex; background-color: {laser_cut_part.paint_item.color}; border-radius: 5px;"></div><span class="tiny-margin">{laser_cut_part.paint_item.name}</span></div>'
        if laser_cut_part.uses_powder and laser_cut_part.powder_item:
            html += f'<div class="no-margin s12"><div class="tiny-margin" style="height: 20px; width: 20px; display: inline-flex; background-color: {laser_cut_part.powder_item.color}; border-radius: 5px;"></div><span class="tiny-margin">{laser_cut_part.powder_item.name}</span></div>'
        if not (
            laser_cut_part.uses_primer
            or laser_cut_part.uses_paint
            or laser_cut_part.uses_powder
        ):
            html = ""
        else:
            html += "</div>"
        return html

    def generate(self) -> str:
        html = '<table class="small-space border dynamic-table responsiveTable"><thead><tr>'
        for i, header in enumerate(self.headers):
            html += f'<th class="small-text {"min" if header != "Process" else ""}" data-column="{i}"><label class="checkbox"><input type="checkbox" class="column-toggle" data-column="{i}" data-name="{header.lower().replace(" ", "-")}" checked><span></span></label>{header}</th>'
        html += "</tr>"
        html += "</thead>"
        html += "<tbody>"
        for laser_cut_part in self.laser_cut_parts:
            unit_price = self.job.price_calculator.get_laser_cut_part_cost(
                laser_cut_part
            )
            html += f"""<tr>
            <td class="min" data-label="{self.headers[0]}" data-column="0" data-name="part">
                <button class="extra transparent small-round" onclick="ui('#LCP-{self.format_filename(laser_cut_part.name)}');">
                    <img class="responsive" src="{self.server_directory}/{laser_cut_part.image_index}">
                    <span class="small-text">{laser_cut_part.name}</span>
                </button>
            </td>
            <td class="min" data-label="{self.headers[1]}" data-column="1" data-name="material"><span class="small-text">{laser_cut_part.gauge}<br>{laser_cut_part.material}</span></td>
            <td data-label="{self.headers[2]}" data-column="2" data-name="process"><span class="small-text">{laser_cut_part.flowtag.get_flow_string()}{self.get_paint(laser_cut_part)}</span></td>
            <td class="small-text left-align" data-label="{self.headers[3]}" data-column="3" data-name="notes"><span class="small-text">{laser_cut_part.notes}</span></td>
            <td data-label="{self.headers[4]}" data-column="4" data-name="shelf-#"><span class="small-text">{laser_cut_part.shelf_number}</span></td>
            <td class="min" data-label="{self.headers[5]}" data-column="5" data-name="unit-qty"><span class="small-text">{laser_cut_part.quantity:,.0f}</span></td>
            <td class="min" data-label="{self.headers[6]}" data-column="6" data-name="qty"><span class="small-text">{(laser_cut_part.quantity * self.assembly_quantity):,.0f}</span></td>
            <td class="min" data-label="{self.headers[7]}" data-column="7" data-name="unit-price"><span class="small-text">${unit_price:,.2f}</span></td>
            <td data-label="{self.headers[8]}" data-column="8" data-name="price"><span class="small-text">${(unit_price * laser_cut_part.quantity * self.assembly_quantity):,.2f}</span></td>
            </tr>"""
        html += f"""<tr>
                <th class="small-text" data-label="{self.headers[0]}" data-column="0" data-name="part"></th>
                <th class="small-text" data-label="{self.headers[1]}" data-column="1" data-name="material"></th>
                <th class="small-text" data-label="{self.headers[2]}" data-column="2" data-name="process"></th>
                <th class="small-text" data-label="{self.headers[3]}" data-column="3" data-name="notes"></th>
                <th class="small-text" data-label="{self.headers[4]}" data-column="4" data-name="shelf-#"></th>
                <th class="small-text" data-label="{self.headers[5]}" data-column="5" data-name="unit-qty"></th>
                <th class="small-text" data-label="{self.headers[6]}" data-column="6" data-name="qty"></th>
                <th class="small-text" data-label="{self.headers[7]}" data-column="7" data-name="unit-price"></th>
                <th class="small-text min" data-label="{self.headers[8]}" data-column="8" data-name="price">Total: ${self.get_total_cost():,.2f}</th>
            </tr></tbody></table>"""
        return html


class ComponentsTable:
    def __init__(self, job: Job, assembly_quantity: int, components: list[Component]):
        self.job = job
        self.assembly_quantity = assembly_quantity
        self.components = components
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.headers = [
            "Part",
            "Part #",
            "Notes",
            "Shelf #",
            "Unit Qty",
            "Qty",
            "Unit Price",
            "Price",
        ]

    def format_filename(self, s: str):
        valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
        filename = "".join(c for c in s if c in valid_chars)
        return filename.replace(" ", "_")

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
            total += (
                self.job.price_calculator.get_component_cost(component)
                * component.quantity
                * self.assembly_quantity
            )
        return total

    def generate(self):
        html = '<table class="small-space border responsiveTable"><thead><tr>'
        for i, header in enumerate(self.headers):
            html += f'<th class="small-text min" data-column="{i}"><label class="checkbox"><input type="checkbox" class="column-toggle" data-column="{i}" data-name="{header.lower().replace(" ", "-")}" checked><span></span></label>{header}</th>'
        html += "</tr></thead><tbody>"
        for component in self.components:
            unit_price = self.job.price_calculator.get_component_cost(component)
            html += f"""<tr>
            <td class="min" data-label="{self.headers[0]}" data-column="0" data-name="part">
                <button class="extra transparent small-round" onclick="ui('#C-{self.format_filename(component.part_name)}');">
                <img class="responsive" src="{self.server_directory}/{component.image_path}">
                <span class="small-text">{component.part_name}</span>
            </td>
            <td class="min" data-label="{self.headers[1]}" data-column="1" data-name="part-#"><span class="small-text">{component.part_number}</span></td>
            <td class="small-text left-align" data-label="{self.headers[2]}" data-column="2" data-name="notes"><span class="small-text">{component.notes}</span></td>
            <td data-label="{self.headers[3]}" data-column="3" data-name="shelf-#"><span class="small-text">{component.shelf_number}</span></td>
            <td class="min" data-label="{self.headers[4]}" data-column="4" data-name="unit-qty"><span class="small-text">{component.quantity:,.0f}</span></td>
            <td class="min" data-label="{self.headers[5]}" data-column="5" data-name="qty"><span class="small-text">{(component.quantity * self.assembly_quantity):,.0f}</span></td>
            <td class="min" data-label="{self.headers[6]}" data-column="6" data-name="unit-price"><span class="small-text">${unit_price:,.2f}</span></td>
            <td data-label="{self.headers[7]}" data-column="7" data-name="price">${(unit_price * component.quantity * self.assembly_quantity):,.2f}</span></td>
            </tr>"""
        html += f"""</tbody><tfoot><tr>
        <th class="small-text" data-label="{self.headers[0]}" data-column="0" data-name="picture"></th>
        <th class="small-text" data-label="{self.headers[1]}" data-column="1" data-name="part-#"></th>
        <th class="small-text" data-label="{self.headers[2]}" data-column="2" data-name="notes"></th>
        <th class="small-text" data-label="{self.headers[3]}" data-column="3" data-name="shelf-#"></th>
        <th class="small-text" data-label="{self.headers[4]}" data-column="4" data-name="unit-qty"></th>
        <th class="small-text" data-label="{self.headers[5]}" data-column="5" data-name="qty"></th>
        <th class="small-text" data-label="{self.headers[6]}" data-column="6" data-name="unit-price"></th>
        <th class="small-text min" data-label="{self.headers[7]}" data-column="7" data-name="price">Total: ${self.get_total_cost():,.2f}</th>
        </tr></tfoot></table>"""
        return html


class AssemblyTable:
    def __init__(self, job: Job):
        self.headers = ["Image", "Assembly Name", "Qty", "Process"]
        self.job = job
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def format_filename(self, s: str):
        valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
        filename = "".join(c for c in s if c in valid_chars)
        return filename.replace(" ", "_")

    def generate_assembly_data(self, assembly: Assembly) -> str:
        html = """<table class="no-space border"><tbody>
                <tr>
                   <td class="small-text bold">Key</td>
                   <td class="small-text">Value</td>
                </tr>"""
        for key, value in assembly.to_dict().get("assembly_data", {}).items():
            html += f"""<tr>
                <td class="small-text bold">{key.replace("_", " ").title()}</td>
                <td class="small-text">{value}</td>
                </tr>"""
        html += "</tbody></table><br>"
        return html

    def generate_assembly_popups(self):
        return "".join(
            f"""
            <div class="overlay blur"></div>
            <dialog style="width: 30vw;" class="right" id="A-{self.format_filename(assembly.name)}">
                <img src="{self.server_directory}/{assembly.assembly_image}" style="height: 100px; width: 100px;" >
                <h5>{assembly.name}</h5>
                <div>{self.generate_assembly_data(assembly)}</div>
                <nav class="right-align no-space">
                    <button data-ui="#A-{self.format_filename(assembly.name)}" class="transparent link">Close</button>
                </nav>
            </dialog>"""
            for assembly in self.job.get_all_assemblies()
        )

    def generate(self) -> str:
        html = """<div id="assemblies-list-layout">
                <h5 class="center-align">Assemblies:</h5>
                <article class="assembly-table border">"""
        if not self.job.get_all_assemblies():
            html += "Nothing here"
        else:
            for assembly in self.job.get_all_assemblies():
                html += f"""
                <a class="row tiny-padding ripple" onclick="ui('#A-{self.format_filename(assembly.name)}');">
                    <img src="{self.server_directory}/image/{assembly.assembly_image}" class="assembly_image round">
                    <div class="max">
                        <h6>{assembly.name}</h6>
                        <div id="assembly-proess-layout">{assembly.flowtag.get_flow_string()}</div>
                    </div>
                    <h5>× {assembly.quantity:,.0f}</h5>
                </a><div class="divider"></div>"""
        html += "</article></div><br>"
        return html


class JobDiv:
    def __init__(self, job: Job):
        self.job = job

    def generate(self) -> str:
        html = ""
        for assembly in self.job.assemblies:
            group_div = AssemblyDiv(self.job, assembly)
            html += group_div.generate()
        return html


class AssemblyDiv:
    def __init__(self, job: Job, assembly: Assembly, use_recursion=True):
        self.job = job
        self.assembly = assembly
        self.use_recursion = use_recursion
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def get_assembly_data_html(self) -> str:
        html = '<div class="assembly_data">'
        image_html = (
            f'<img class="assembly-image" src="{self.server_directory}/image/{self.assembly.assembly_image}">'
            if self.assembly.assembly_image
            else ""
        )
        html += image_html
        html += '<div class="padding">'
        html += f"<h5>{self.assembly.name}</h5>"
        html += f'<p class="small-text">Assembly Quantity: {self.assembly.quantity:,.0f}</p>'
        html += f'<p class="small-text">Process: {self.assembly.flowtag.get_flow_string()}</p>'
        html += f'<p class="small-text">Paint: {self.get_paint()}</p>'
        html += "</div>"
        html += "</div>"
        return html

    def generate(self) -> str:
        html = '<details class="assembly_details" open>'
        html += (
            f"<summary>{self.assembly.name} × {self.assembly.quantity:,.0f}</summary>"
        )
        html += '<div class="assembly">'
        html += self.get_assembly_data_html()

        if self.assembly.laser_cut_parts:
            html += '<details class="laser_cut_parts_detail" open>'
            html += "<summary>Laser Cut Parts</summary>"
            html += '<div class="detail_contents laser_cut_part_contents">'
            laser_cut_table = LaserCutPartsTable(
                self.job, self.assembly.quantity, self.assembly.laser_cut_parts
            )
            html += laser_cut_table.generate()
            html += "</div>"
            html += "</details>"

        if self.assembly.components:
            html += '<details class="components_detail" open>'
            html += "<summary>Components</summary>"
            html += '<div class="detail_contents components_contents">'
            component_table = ComponentsTable(
                self.job, self.assembly.quantity, self.assembly.components
            )
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
                sub_assembly_div = AssemblyDiv(self.job, sub_assembly)
                html += sub_assembly_div.generate()
            html += "</div>"
            html += "</details>"

        html += "</div>"
        html += "</details>"
        return html

    def get_paint(self) -> str:
        html = '<div class="no-padding small-text">'
        if self.assembly.uses_primer and self.assembly.primer_item:
            html += f'<div class="row no-margin"><div style="height: 20px; width: 20px; background-color: {self.assembly.primer_item.color}; border-radius: 5px;"></div>{self.assembly.primer_item.name}</div>'
        if self.assembly.uses_paint and self.assembly.paint_item:
            html += f'<div class="row no-margin"><div style="height: 20px; width: 20px; background-color: {self.assembly.paint_item.color}; border-radius: 5px;"></div>{self.assembly.paint_item.name}</div>'
        if self.assembly.uses_powder and self.assembly.powder_item:
            html += f'<div class="row no-margin"><div style="height: 20px; width: 20px; background-color: {self.assembly.powder_item.color}; border-radius: 5px;"></div>{self.assembly.powder_item.name}</div>'
        if not (
            self.assembly.uses_primer
            or self.assembly.uses_paint
            or self.assembly.uses_powder
        ):
            html = ""
        else:
            html += "</div>"
        return html


class JobParts:
    def __init__(self, job: Job):
        self.job = job

    def generate(self) -> str:
        return ""


class PrintoutHeader:
    def __init__(
        self,
        name: str,
        printout_type: Literal["QUOTE", "WORKORDER", "PACKINGSLIP"] = "QUOTE",
    ):
        self.name = name
        self.printout_type = printout_type
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.html = f"""<header class="surface">
            <nav class="row">
                <img class="logo" src="{self.server_directory}/images/logo.png">
                <h5 class="max center-align small">
                    {self.name}
                </h5>
                <div class="date">
                    {str(datetime.now().strftime("%I:%M:%S %p %A %B %d, %Y"))}
                </div>
                <button class="circle transparent" id="theme-toggle">
                    <i id="theme-icon">dark_mode</i>
                </button>
            </nav>
            <nav class="tabbed primary-container">
                <a {'class="active primary"' if self.printout_type == "QUOTE" else ''} data-target="quote">
                    <i>request_quote</i>
                    <span>Quote</span>
                </a>
                <a {'class="active primary"' if self.printout_type == "WORKORDER" else ''} data-target="workorder">
                    <i>construction</i>
                    <span>Workorder</span>
                </a>
                <a {'class="active primary"' if self.printout_type == "PACKINGSLIP" else ''} data-target="packingslip">
                    <i>receipt_long</i>
                    <span>Packing Slip</span>
                </a>
            </nav>
        </header>"""


class WorkspaceJobPrintout:
    def __init__(
        self,
        job: Job,
        printout_type: Literal["QUOTE", "WORKORDER", "PACKINGSLIP"] = "QUOTE",
    ):
        self.job = job
        self.printout_type = printout_type
        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def generate(self) -> str:
        header_html = PrintoutHeader(self.job.name, self.printout_type).html
        head_html = Head(
            f"{self.printout_type.title()} - {self.job.name}", self.job.ship_to
        ).html
        html = f"""<!DOCTYPE html>
                <html>{head_html}
        <body class="{self.printout_type.lower()}">
            <nav class="drawer left border" style="align-content: center" id="printout-controls">
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showCoverPage" data-name="show-cover-page" data-layout="cover-page" checked>
                        <span>Show Cover Page</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showAssemblies" data-name="show-assemblies" data-layout="assemblies-list-layout" {"checked" if self.job.assemblies else ""}>
                        <span>Show Assemblies</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showAssemblyProcess" data-name="show-assembly-process" data-layout="assembly-proess-layout" checked>
                        <span>Show Assembly Process</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showNests" data-name="show-nests" data-layout="nests-layout" {"checked" if self.job.nests else ""}>
                        <span>Show Nests</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showSheets" data-name="show-sheets" data-layout="sheets-layout" {"checked" if self.job.nests else ""}>
                        <span>Show Sheets</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showNestedParts" data-name="show-nested-parts" data-layout="nested-parts-layout">
                        <span>Show Nested Parts</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showParts" data-name="show-parts" data-layout="parts-layout" {"checked" if self.job.get_all_components() or self.job.get_all_laser_cut_parts() else ""}>
                        <span>Show Parts</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showTotalCost" data-name="show-total-cost" data-layout="total-cost-layout" checked>
                        <span>Show Total Cost</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showNetWeight" data-name="show-net-weight" data-layout="net-weight-layout" checked>
                        <span>Show Net Weight</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="usePageBreaks" data-name="use-page-breaks" data-layout="page-break" checked>
                        <span>Use Page Breaks</span>
                    </label>
                </a>
            </nav>
            <main class="responsive">
            {header_html}<br>
        """

        cover_page = CoverPage(
            self.job.order_number,
            self.job.PO_number,
            self.job.starting_date,
            self.job.ending_date,
            self.job.ship_to,
        )

        html += cover_page.generate()

        all_assemblies = self.job.get_all_assemblies()

        assembly_table = AssemblyTable(self.job)
        html += assembly_table.generate()

        sheets_table = NestsTable(self.job.nests)
        html += sheets_table.generate()

        nests_table = SheetImages(self.job.nests)
        html += nests_table.generate()

        nested_parts = NestedLaserCutParts(self.job.nests)
        html += nested_parts.generate()

        html += '<div id="parts-layout">'
        html += """<div class="tabs scroll">
            <a data-ui="#assemblies-layout"><i>table_view</i>Nested Layout</a>
            <a class="active" data-ui="#assemblies-list"> <i>data_table</i>Assemblies List</a>
            <a data-ui="#parts-list"> <i>format_list_bulleted</i>Grouped Parts List</a>
        </div>"""
        html += '<div class="page" id="assemblies-layout">'
        if self.job.assemblies:
            job_div = JobDiv(self.job)
            html += job_div.generate()
        else:
            html += "Nothing here"
        html += "</div>"

        html += '<div class="page active" id="assemblies-list" >'
        if all_assemblies:
            for index, assembly in enumerate(all_assemblies):
                assembly_div = AssemblyDiv(self.job, assembly, False)
                html += assembly_div.generate()
                if index < len(all_assemblies) - 1:  # Check if it's not the last item
                    html += '<div id="page-break" class="page-break"></div>'
        else:
            html += "Nothing here"
        html += "</div>"

        grouped_laser_cut_parts = self.job.get_grouped_laser_cut_parts()
        grouped_laser_cut_parts_table = LaserCutPartsTable(
            self.job, 1, grouped_laser_cut_parts
        )

        grouped_components = self.job.get_grouped_components()
        grouped_components_table = ComponentsTable(self.job, 1, grouped_components)

        html += '<div class="page" id="parts-list">'
        if grouped_laser_cut_parts or grouped_components:
            if grouped_laser_cut_parts:
                html += '<h5 class="center-align">Laser Cut Parts:</h5>'
                html += grouped_laser_cut_parts_table.generate()
            if grouped_components:
                html += '<h5 class="center-align">Components:</h5>'
                html += grouped_components_table.generate()
        else:
            html += "Nothing here"
        html += "</div>"
        html += "</div>"  # for the tabs

        if grouped_components or grouped_laser_cut_parts:
            html += f"""
            <div class="grid row max center-align">
                <div id="net-weight-layout" class="s6">
                    <h6 class="center-align bold">Net Weight: {self.job.get_net_weight():,.2f} lb</h6>
                </div>
                <div id="total-cost-layout" class="s6">
                    <h6 class="center-align bold">Total Cost: ${self.job.price_calculator.get_job_cost():,.2f}</h6>
                    <p class="small-text no-margin center-align bold underline">No tax is included in this quote.</p>
                    <p class="small-text no-margin center-align">Payment past due date will receive 1.5% interest rate per month of received goods.</p>
                </div>
            </div>"""

        if grouped_laser_cut_parts:
            html += grouped_laser_cut_parts_table.generate_laser_cut_part_popups()
        if grouped_components:
            html += grouped_components_table.generate_components_popups()
        html += assembly_table.generate_assembly_popups()
        html += nests_table.generate_laser_cut_part_popups()

        html += "</main></body>"
        return html


class WorkorderPrintout:
    def __init__(
        self,
        nests: list[Nest],
        workorder_id: str,
        should_include_qr_to_workorder: bool,
        printout_type: Literal["QUOTE", "WORKORDER", "PACKINGSLIP"] = "WORKORDER",
    ):
        self.nests = nests
        for nest in self.nests:
            nest.sort_laser_cut_parts()
        self.sorted_nests = natsorted(self.nests, key=lambda nest: nest.get_name())
        self.sorted_nests_reversed = natsorted(
            self.nests, key=lambda nest: nest.get_name(), reverse=True
        )

        self.workorder_id = workorder_id
        self.printout_type = printout_type
        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"
        self.should_include_qr_to_workorder = should_include_qr_to_workorder

    def generate(self) -> str:
        header_html = PrintoutHeader("Nested Parts", self.printout_type).html
        head_html = Head(
            f"{self.printout_type.title()} - Nest Printout", "Workspace Nest Printout"
        ).html
        html = f"""<!DOCTYPE html>
                <html>{head_html}
        <body class="{self.printout_type.lower()}">
            <nav class="drawer left border" style="align-content: center" id="printout-controls">
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showNests" data-name="show-nests" data-layout="nests-layout" {"checked" if self.nests else ""}>
                        <span>Show Nests</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showSheets" data-name="show-sheets" data-layout="sheets-layout" {"checked" if self.nests else ""}>
                        <span>Show Sheets</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showNestedParts" data-name="show-nested-parts" data-layout="nested-parts-layout">
                        <span>Show Nested Parts</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="showRecutPartsSummary" data-name="show-recut-parts-summary" data-layout="recut-parts-summary-layout">
                        <span>Show Recut Parts Summary</span>
                    </label>
                </a>
                <a class="surface-container">
                    <label class="checkbox">
                        <input type="checkbox" id="usePageBreaks" data-name="use-page-breaks" data-layout="page-break">
                        <span>Use Page Breaks</span>
                    </label>
                </a>
            </nav>
        <main class="responsive">
        {header_html}<br>"""

        html += '<div class="row">'
        all_nest_notes = "".join(nest.notes for nest in self.sorted_nests)
        if all_nest_notes:
            nest_recut_part_summary = NestRecutPartSummary(self.sorted_nests)
            html += nest_recut_part_summary.generate()
        if self.should_include_qr_to_workorder:
            workorder_id = WorkorderID(self.workorder_id)
            html += workorder_id.generate()
        html += "</div>"

        sheets_table = NestsTable(self.sorted_nests)
        html += sheets_table.generate()

        nests_table = SheetImages(self.sorted_nests)
        html += nests_table.generate()

        nested_parts = NestedLaserCutParts(self.sorted_nests_reversed)
        html += nested_parts.generate()

        html += nests_table.generate_laser_cut_part_popups()

        html += "</main></body>"
        return html
