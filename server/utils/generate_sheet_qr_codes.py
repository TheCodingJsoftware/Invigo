import shutil
import urllib.parse
from pathlib import Path

import qrcode  # pip install qrcode
import json
import xlsxwriter
from qrcode import constants

with open(
    r"C:\Users\Invigo\Inventory-Manager\server\data\inventory - Price of Steel.json",
    "r",
) as f:
    data = json.load(f)

FONT_NAME: str = "Book Antiqua"
SERVER_IP: str = "10.0.0.9"
SERVER_PORT: int = 8080

workbook = xlsxwriter.Workbook("qr_codes.xlsx")
workbook.set_properties(
    {
        "title": "QR Codes",
        "subject": "For Sheets in Inventory",
        "author": "Jared Gross",
        "manager": "Jared Gross",
        "company": "TheCodingJsoftware",
        "category": "Qr Codes",
        "keywords": "QR, Codes, Sheets",
        "comments": "Created with Love, Python and XlsxWriter",
    }
)
worksheet = workbook.add_worksheet()
worksheet.set_column(0, 1, 50)  # Set column A and B width to 15
worksheet.hide_gridlines(2)
worksheet.set_margins(0.25, 0.25, 0.25, 0.25)

row, col = 1, 1
merge_format = workbook.add_format({"align": "center", "bold": True, "font_size": 16, "font_name": FONT_NAME})
text_format = workbook.add_format({"align": "center", "valign": "top", "bold": True, "font_name": FONT_NAME})
Path("qr_codes").mkdir(parents=True, exist_ok=True)

for category in data:
    if category in ["Price Per Pound", "Cutoff"]:
        continue
    # worksheet.merge_range(f"A{row}:B{row}", category, merge_format)
    for sheet in data[category]:
        base_url = f"http://{SERVER_IP}:{SERVER_PORT}/sheets_in_inventory/{sheet}".replace(" ", "_")
        encoded_url = urllib.parse.quote(base_url, safe=":/")
        qr = qrcode.QRCode(error_correction=constants.ERROR_CORRECT_H, box_size=10, border=1)
        qr.add_data(encoded_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img_path = f"qr_codes/{sheet.replace('/', '.')}.png"
        qr_img.save(qr_img_path)
        # Insert the QR code image into the worksheet
        worksheet.insert_image(
            row,
            col,
            qr_img_path,
            {
                "x_offset": 50,
                "y_offset": 30,
                "x_scale": 0.45,
                "y_scale": 0.45,
                "align": "center",
                "valign": "top",
            },
        )

        worksheet.set_row(row, 205)  # Set row 0 (header row) height to 20
        row += 1
        worksheet.write(row, col, sheet, text_format)
        worksheet.set_row(row, 24)  # Set row 0 (header row) height to 20
        col += 1
        row += 1
        if col == 2:
            col = 0
            row -= 2
workbook.close()
shutil.rmtree("qr_codes")
