> A multi-user, state-of-the-art assembly-based Inventory Manager, designed to streamline the process of component tracking, management and quoting.

<table>
<tbody>
<td>
<img style="border-radius: 25px; max-width: 200px; width: auto; height: 150px" src="icons/icon.png" /><p style="font-size: 36px; font-weight: bold; max-width: 200px; text-align: center; margin: auto;">Invigo</p>
</td>
<td>
<img src="https://img.shields.io/github/created-at/TheCodingJsoftware/Inventory-Manager?style=for-the-badge&"/><img src="https://img.shields.io/github/license/TheCodingJsoftware/Inventory-Manager?&style=for-the-badge"/><img src="https://img.shields.io/static/v1?label=Platform&message=Windows&&style=for-the-badge"/><img src="https://img.shields.io/github/repo-size/TheCodingJsoftware/Inventory-Manager?label=Size&style=for-the-badge"/><img src="https://img.shields.io/github/commit-activity/m/TheCodingJsoftware/Inventory-Manager?style=for-the-badge"/><img src="https://img.shields.io/github/last-commit/TheCodingJsoftware/Invigo?style=for-the-badge
"/><img src="https://img.shields.io/github/languages/count/TheCodingJsoftware/Inventory-Manager?style=for-the-badge"><img src="https://img.shields.io/github/languages/top/TheCodingJsoftware/Inventory-Manager?style=for-the-badge"><img src="https://img.shields.io/badge/python-3.12-blue?style=for-the-badge">

<img src="https://ForTheBadge.com/images/badges/made-with-python.svg"><img src="https://forthebadge.com/images/badges/powered-by-qt.svg"><img src="https://ForTheBadge.com/images/badges/built-with-love.svg">
</td>
</tbody>
</table>

# Development Setup

1. Download [python](https://www.python.org/downloads/).
2. Clone this repository with: `git clone https://github.com/TheCodingJsoftware/Invigo`
3. Create a virtual environemt with: `virtualenv venv`
4. Active your virtual environment.
5. Install requirements with: `pip install -r requirements.txt`
6. Run with `python main.py`

# Invigo-Web

[Invigo-Web](https://github.com/TheCodingJsoftware/Invigo-Web) is a web portal that handles updates and latest versions.

# Invigo-Server

[Invigo-Server](https://github.com/TheCodingJsoftware/Invigo-Server) is a LAN Server that handles HTTP requests from [Invigo](https://github.com/TheCodingJsoftware/Invigo).

NOTE: [Invigo-Server](https://github.com/TheCodingJsoftware/Invigo-Server) is **required** for [Invigo](https://github.com/TheCodingJsoftware/Invigo) to work.

It also hosts various web pages that are designed with [beercss](https://beercss.com):

 - `/` is the homepage.
 - `/server_log` is the live server log that also shows connected users.
 - `/logs` is a page where you can view user error logs and past server logs.
 - `/inventory` you can view all inventories and their respective categories.
 - `/inventory/(.*)/(.*)` is a table that loads all inventory items from the selected inventory and category.
   - Example: `/inventory/components_inventory/BL 25` will load a table of all the items in the `components_inventory` that are in the `BL 25` category.
 - `/sheets_in_inventory/(.*)` is a page where you can view the order-pending status of a sheet and view/edit the quantity.
 - `/sheet_qr_codes` is a printer-ready page that generates QR Codes for every sheet in the inventory, scanning the QR Code redirects you to `/sheets_in_inventory/(.*)`.
 - `/add_cutoff_sheet` is a page to add and vew cutoff sheets.
 - `/load_job/(.*)` loads a jobs HTML contents.
 - `/load_quote/(.*)` loads a quotes HTML contents.