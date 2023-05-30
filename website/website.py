"""
This script is seperate from the entire client-end project
and is not intended for the client to use this script.
"""

import contextlib
import json
import os
import threading
import time
from datetime import datetime

import requests
from flask import Flask, render_template
from forex_python.converter import CurrencyRates

app = Flask(__name__)


def write_log(log: str) -> None:
    pass
    # with open(f"{os.path.dirname(os.path.realpath(__file__))}/log.txt", 'a') as f:
    #     f.write(log +'\n')

@app.route("/")
def index() -> None:
    """
    It renders the index.html template with the variables downloadableRecordings, searchValue,
    colonySearchList, monthsList, daysList, and recordingStatus
    Returns:
      The webpage
    """
    write_log('Loading website')
    try:
        #return f"<span style='color:red'>{os.path.dirname(os.path.realpath(__file__))}</span>"
        downloadDatabase()
        inventory = sort_groups(get_inventory_data())
        #return render_template("index.html")
        #inventory = {}
        return render_template(
            "index.html",
            search_term="",
            inventory=inventory,
            part_names=get_all_part_names(),
            part_numbers=get_all_part_numbers(),
            unit_costs=get_all_unit_cost(),
            last_updated=str(time.strftime('Database last updated on %A %B %d %Y at %I:%M:%S %p',time.localtime(os.path.getmtime(f"{os.path.dirname(os.path.realpath(__file__))}/inventory.json")))),
            price_of_steel=get_price_of_steel(),
        )
    except Exception as e:
        write_log(f"<span style='color:red'>{e}</span>")


@app.route("/<search_term>")
def search(search_term):
    """Main page
    Returns:
        _type_: webpage
    """
    downloadDatabase()
    inventory = sort_groups(get_inventory_data())
    search_term = search_term.replace("_", " ")
    for category in list(inventory.keys()):
        for group in list(inventory[category].keys()):
            for item_name in list(inventory[category][group].keys()):
                try:
                    part_name = inventory[category][group][item_name][
                        "part_number"
                    ].replace("/", "_")
                    if not (
                        search_term.lower().replace("/", "⁄")
                        in item_name.lower().replace("/", "⁄")
                        or search_term.lower().replace("/", "_") in part_name.lower()
                    ):
                        inventory[category][group].pop(item_name)
                except KeyError:
                    continue

    for category in list(inventory.keys()):
        for group in list(inventory[category].keys()):
            if len(inventory[category][group]) == 0:
                inventory[category].pop(group)

    for category in list(inventory.keys()):
        if len(inventory[category]) == 0:
            inventory.pop(category)

    return render_template(
        "index.html",
        inventory=inventory,
        search_term=search_term.replace(" ", "_"),
        part_names=get_all_part_names(),
        part_numbers=get_all_part_numbers(),
        unit_costs=get_all_unit_cost(),
        last_updated=str(time.strftime('Database last updated on %A %B %d %Y at %I:%M:%S %p',time.localtime(os.path.getmtime(f"{os.path.dirname(os.path.realpath(__file__))}/inventory.json")))),
        price_of_steel=get_price_of_steel(),
    )


def get_price_of_steel() -> dict:
    """
    It opens the file "inventory - Price of Steel.json" and returns the value of the key "Price Per
    Pound"

    Returns:
      A dictionary of the price of steel.
    """
    price_of_steel = {}
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/inventory - Price of Steel.json", "r") as f:
        data = json.load(f)
    return data["Price Per Pound"]


def sort_groups(category: dict) -> dict:
    """
    It takes a dictionary of dictionaries, and returns a dictionary of dictionaries, where the keys
    of the returned dictionary are the values of the "group" key in the original dictionary
    Args:
        category (dict): dict
    Returns:
        A dictionary with the keys being the group names and the values being a dictionary of the
    items in that group.
    """
    grouped_category: dict = {}
    for category_name in list(category.keys()):
        grouped_category[category_name] = {}
        for item in category[category_name].items():
            with contextlib.suppress(KeyError):
                if item[1]["group"] and item[1]["group"] != "":
                    grouped_category[category_name][item[1]["group"]] = {}
        grouped_category[category_name]["Everything else"] = {}

    for category_name in list(category.keys()):
        for item in category[category_name].items():
            try:
                if item[1]["group"] and item[1]["group"] != "":
                    grouped_category[category_name][item[1]["group"]][item[0]] = item[1]
            except Exception:
                grouped_category[category_name]["Everything else"][item[0]] = item[1]

    return grouped_category


def get_all_unit_cost() -> dict:
    data = get_inventory_data()
    currency_rates = CurrencyRates()
    try:
        last_exchange_rate = currency_rates.get_rate("USD", "CAD")
    except Exception:
        last_exchange_rate = 1.3608673726676752  # just a guess
    unit_costs = {}
    for category in list(data.keys()):
        total_cost: float = 0
        unit_costs[category] = {}
        with contextlib.suppress(KeyError):
            for item in data[category]:
                use_exchange_rate: bool = data[category][item]["use_exchange_rate"]
                exchange_rate: float = last_exchange_rate if use_exchange_rate else 1
                price: float = data[category][item]["price"]
                unit_quantity: int = data[category][item]["unit_quantity"]
                total_cost += price * unit_quantity * exchange_rate
            unit_costs[category] = f'{total_cost:,.2f}'
    return unit_costs


def get_all_part_names() -> list[str]:
    """
    It takes the data from the self.inventory module, loops through the data, and returns a list of all
    the part names
    Returns:
      A list of all the part names in the self.inventory.
    """
    data = get_inventory_data()
    part_names = []
    for category in list(data.keys()):
        part_names.extend(
            item.replace(" ", "_").replace("/", "⁄")
            for item in list(data[category].keys())
        )
    return list(set(part_names))


def get_all_part_numbers() -> list[str]:
    """
    It takes the data from the self.inventory module, loops through the data, and returns a list of all
    the part numbers
    Returns:
      A list of all the part numbers in the self.inventory.
    """
    data = get_inventory_data()
    part_numbers = []
    for category in list(data.keys()):
        try:
            part_numbers.extend(
                data[category][item]["part_number"].replace(" ", "_").replace("/", "⁄")
                for item in list(data[category].keys())
            )
        except KeyError:
            continue

    return list(set(part_numbers))


def get_inventory_data() -> dict:
    """loads inventory.json file
    Returns:
        dict: json file for all the download links
    """
    try:
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/inventory.json", "r") as inventory_file:
            data = json.load(inventory_file)
        return data
    except Exception as e:
        write_log(f'Failed to load inventory.json - {e}')
        return {}


def downloadDatabase() -> None:
    """downloads the inventory.json file from github"""
    files_to_download: dict[list[str, str]] = {
        "inventory.json": "https://raw.githubusercontent.com/TheCodingJsoftware/Inventory-Manager/master/server/data/inventory.json",
        "inventory - Price of Steel.json": "https://raw.githubusercontent.com/TheCodingJsoftware/Inventory-Manager/master/server/data/inventory - Price of Steel.json",
    }
    for file in list(files_to_download.keys()):
        print(f'Downloading {file}')
        try:
            req = requests.get(files_to_download[file])
            if req.status_code == requests.codes.ok:
                data = req.json()  # the response is a JSON
                with open(f"{os.path.dirname(os.path.realpath(__file__))}/{file}", "w+") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            write_log(f'{e}')
    write_log('download database')

def downloadThread() -> None:
    """update database every 5 minutes"""
    while True:
        downloadDatabase()
        time.sleep(300)


#downloadThread()
#threading.Thread(target=downloadThread).start()
app.run(host="10.0.0.217", port=5000, debug=False, threaded=True)
