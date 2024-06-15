import configparser
import copy
import os
import sys
from datetime import datetime

from utils.ip_utils import get_server_ip_address, get_server_port
from utils.quote.generate_quote import ComponentsTable, CoverPage, LaserCutPartsTable
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job
from utils.workspace.group import Group
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_item import WorkspaceItem

# class AssemblyTable:
#     def __init__(self, data: dict[Assembly, int]):
#         self.headers = ["Image", "Assembly Name", "Qty", "Flow Tag"]
#         self.data = data
#         self.server_directory = f"http://{get_server_ip_address()}"

#     def generate(self) -> str:
#         html = "<table class='ui-responsive' data-mode='' data-role='table' id='data-table' style='border-collapse: collapse; text-align: center; vertical-align: middle; font-size: 12px;'>"
#         html += "<tr class='header-table-row'>"
#         for header in self.headers:
#             html += f"<th>{header}</th>"
#         html += "</tr>"
#         html += '<tbody id="table-body">'
#         for assembly, data in self.data.items():
#             flow_tag = assembly.flow_tag.get_name()
#             assembly_image_path = assembly.assembly_image
#             image_html = f'<img src="{self.server_directory}/{assembly_image_path}" alt="Image" class="nest_image" id="{self.server_directory}/{assembly_image_path}">' if assembly_image_path else "No image provided"
#             html += "<tr>" f'<td class="ui-table-cell-visible">{image_html}</td>' f'<td class="ui-table-cell-visible">{assembly.name}</td>' f'<td class="ui-table-cell-visible">{data["quantity"]}</td>' f'<td class="ui-table-cell-visible">{flow_tag}</td>' "</tr>"
#         html += "</tbody></table>"
#         return html


class AssemblyTable:
    def __init__(self, job: Job):
        self.headers = ["Image", "Assembly Name", "Qty", "Process"]
        self.job = job
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def generate(self) -> str:
        html = "<table class='ui-responsive' data-mode='' data-role='table' id='data-table' style='border-collapse: collapse; text-align: center; vertical-align: middle; font-size: 12px;'>"
        html += "<tr class='header-table-row'>"
        for header in self.headers:
            html += f"<th>{header}</th>"
        html += "</tr>"
        html += '<tbody id="table-body">'
        for assembly in self.job.get_all_assemblies():
            flow_tag = assembly.flow_tag.get_name()
            image_html = f'<img src="{self.server_directory}/image/{assembly.assembly_image}" alt="Assembly Image" class="assembly_image" id="{self.server_directory}/image/{assembly.assembly_image}">' if assembly.assembly_image else ""
            html += f'''<tr>
                <td class="ui-table-cell-visible">{image_html}</td>
                <td class="ui-table-cell-visible">{assembly.name}</td>
                <td class="ui-table-cell-visible">NA</td>
                <td class="ui-table-cell-visible">{flow_tag}</td>
                </tr>'''
        html += "</tbody></table>"
        return html


class JobDiv:
    def __init__(self, job: Job) -> None:
        self.job = job

    def generate(self) -> str:
        html = ""
        # html = "<details open>"
        # html += f"<summary>{self.job.name}</summary>"
        # html += '<div class="job">'
        for group in self.job.groups:
            group_div = GroupDiv(group)
            html += group_div.generate()
        # html += "</div>"
        # html += "</details>"
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
    def __init__(self, assembly: Assembly) -> None:
        self.assembly = assembly
        self.server_directory = f"http://{get_server_ip_address()}:{get_server_port()}"

    def get_assembly_data_html(self) -> str:
        html = '<div class="assembly_data">'
        image_html = f'<img src="{self.server_directory}/image/{self.assembly.assembly_image}" alt="Assembly Image" class="assembly_image" id="{self.server_directory}/image/{self.assembly.assembly_image}">' if self.assembly.assembly_image else ""
        html += image_html
        html += '<div>'
        html += f"<h2>{self.assembly.name}</h2>"
        html += f"<p>Process: {self.assembly.flow_tag.get_name()}</p>"
        html += '</div>'
        html += '</div>'
        return html

    def generate(self) -> str:
        html = '<details class="assembly_details" open>'
        html += f"<summary>{self.assembly.name}</summary>"
        html += '<div class="assembly">'
        html += self.get_assembly_data_html()

        if self.assembly.laser_cut_parts:
            html += '<details class="laser_cut_parts_detail" open>'
            html += "<summary>Laser Cut Parts</summary>"
            html += '<div class="detail_contents laser_cut_part_contents">'
            laser_cut_table = LaserCutPartsTable("Workorder", self.assembly.laser_cut_parts)
            html += laser_cut_table.generate()
            html += "</div>"
            html += "</details>"

        if self.assembly.components:
            html += '<details class="components_detail" open>'
            html += "<summary>Components</summary>"
            html += '<div class="detail_contents components_contents">'
            component_table = ComponentsTable(self.assembly.components)
            html += component_table.generate()
            html += "</div>"
            html += "</details>"

        if self.assembly.laser_cut_parts or self.assembly.components:
            html += '<div class="page-break"></div>'

        if self.assembly.sub_assemblies:
            html += '<details open>'
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



class JobPlannerPrintout:
    def __init__(
        self,
        job: Job,
    ) -> None:
        self.job = job
        self.title = "Job Plan"
        self.program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))

        with open("utils/workspace/printout.css", "r", encoding="utf-8") as printout_css_file:
            self.printout_css = printout_css_file.read()

        with open("utils/workspace/printout.js", "r", encoding="utf-8") as printout_js_file:
            self.printout_js = printout_js_file.read()

    def generate(self) -> str:
        html = f"""<!DOCTYPE html>
                <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>{self.title} - {self.job.name}</title>
                        <link rel="stylesheet" href="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css">
                        <link href='https://fonts.googleapis.com/css?family=Varela Round' rel='stylesheet'>
                        <script src="https://code.jquery.com/jquery-1.11.3.min.js"></script>
                        <script src="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
                        <script src="https://kit.fontawesome.com/b88fae5da2.js"
                            crossorigin="anonymous"></script>
                    </head>
        <style>{self.printout_css}</style>
        <div data-role="page" id="pageone">"""

        cover_page = CoverPage(self.title, self.job)


        html += cover_page.generate()

        assembly_table = AssemblyTable(self.job)
        html += assembly_table.generate()

        html += '<div class="page-break"></div>'

        job_div = JobDiv(self.job)
        html += job_div.generate()
        html += f'<script>{self.printout_js}</script>'
        return html


#     def generate(self) -> str:
#         assemblies_table = AssemblyTable(self.data)
#         html_start = (
#             """
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="UTF-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <title>"""
#             + self.title
#             + """</title>
#             <link rel="stylesheet" href="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css">
#             <script src="https://code.jquery.com/jquery-1.11.3.min.js"></script>
#             <script src="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
#         </head>
#         <style> """
#             + self.printout_css
#             + """</style>
#         <script>"""
#             + self.printout_js
#             + '''</script>
#         <div data-role="page" id="pageone">
#             <div id="cover-page">
#                 <label for="showCoverPage" id="showCoverPageLabel" style="background-color: #EAE9FC; width: 200px; margin-left: 84%; border: none; margin-top: 10px;">
#                  Show Cover Page
#                 </label>
#                 <input style="background-color: #EAE9FC; display: none;" type="checkbox" id="showCoverPage" checked=true>
#                 <div style="position: absolute; top: 0;">
#                     <img class="logo" src="'''
#             + self.program_directory
#             + """/icons/logo.png" alt="Logo">
#                 </div>
#                 <div class="title">"""
#             + self.title
#             + """</div>
#                 <div class="input-row" style="top: 60px; position: absolute; right: 0; width: 300px;">
#                     <label>
#                     Order #
#                     </label>
#                     <input type="text" class="input-box" id="order-number">
#                 </div>
#                 <div style="margin-bottom: 80px;"></div>
#                 <div class="date"> """
#             + str(datetime.now().strftime("%I:%M:%S %p %A %B %d, %Y"))
#             + """</div>
#                 <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; right: 0; width: 300px;height: 180px; position: absolute; margin: 10px; top: 100px;">
#                     <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px">
#                     Ship To:
#                     <textarea style="resize: none;">


# </textarea>
#             </div>
#         </div>
#             <div style="border: #cccccc; border-radius: 10px; border-width: 1px; border-style: solid; left: 0; width: 400px; height: 180px; position: absolute; margin: 10px; top: 100px;">
#                 <div style="padding-top: 10px; padding-right: 10px; padding-left: 10px">
#                 Date Shipped:
#                     <input class="input-box" type="text" value=""></input>
#                 Date Expected:
#                 <input class="input-box" type="text" value=""></input>
#                 Received in good order by:
#                     <input class="input-box" type="text" value=""></input>
#                 </div>
#             </div>
#             <div style="margin-bottom: 300px;"></div>
#         </div>
#                 <details id="assemblies-toggle" class="assemblies-toggle">
#                     <summary style="font-size: 24px; text-align: center; margin-top: 20px;">Assemblies</summary>
#                     """
#             + assemblies_table.generate()
#             + """
#                     <div class="page-break"></div>
#                 </details>
#         <div data-role="main" class="ui-content">
#         """
#         )
#         html = html_start

#         def get_items_table(assembly: Assembly) -> str:
#             text = ""
#             if assembly in list(self.data.keys()):
#                 assembly_flow_tag = " ➜ ".join(assembly.flow_tag)
#                 assembly_image_path = assembly.assembly_image
#                 items_table = ItemsTable(
#                     assembly,
#                     self.data[assembly]["quantity"],
#                     self.data[assembly]["show_all_items"],
#                 )
#                 image_html = f'<img src="{self.program_directory}/{assembly_image_path}" alt="Image" class="nest_image" id="{self.program_directory}/{assembly_image_path}">' if assembly_image_path else ""
#                 text += '<div style="margin: 15px; padding: 5px; border: 1px solid #bbb; border-radius: 10px; page-break-inside: avoid;">'
#                 text += f'<div style="display: inline-flex;">{image_html}<div><h2 style="margin: 0;">{assembly.name} x {self.data[assembly]["quantity"]}</h2><p>Flow Tag: {assembly_flow_tag}</p></div></div>'
#                 if len(assembly.items) > 0:
#                     text += items_table.generate()
#             for sub_assembly in assembly.sub_assemblies:
#                 text += get_items_table(sub_assembly)
#             if assembly in list(self.data.keys()):
#                 text += "</div>"
#             return text

#         for assembly in self.admin_workspace.data:
#             html += get_items_table(assembly)

#         html += "</div></html>"

#         return html
