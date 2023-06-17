import ujson as json
import urllib.parse


with open(r"F:\Code\Python-Projects\Inventory Manager\data\inventory - Price of Steel.json", "r") as f:
    data = json.load(f)


for category in data:
    if category == "Price Per Pound":
        continue
    for sheet in data[category]:
        with open("sheets_output.txt", "a") as f:

            base_url = f"http://10.0.0.93/sheets_in_inventory/{sheet}".replace(" ", "_")
            encoded_url = urllib.parse.quote(base_url, safe=":/")
            f.write(f'=IMAGE("https://quickchart.io/qr?text={encoded_url}"\t{sheet}' + "\n")
