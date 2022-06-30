import os
import re

import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import QThread, pyqtSignal


class EbayScraper(QThread):
    """This class is a QThread that scrapes ebay for a given search term and returns the results in a list"""

    signal = pyqtSignal(object)

    def __init__(self, item_to_search: str) -> None:
        """
        The function takes in a string, and then uses that string to create a url that will be used to
        search for the item on ebay

        Args:
          item_to_search (str): str = item to search
        """
        QThread.__init__(self)
        self.item_to_search: str = item_to_search
        self.TITLE_REGEX = r'<h3 class="s-item__title">([\w|\W]{1,})<\/h3>'
        self.PRICE_REGEX = r'<span class="s-item__price">\n\s{1,100}(\$\d{1,}\.\d{1,2})'
        self.SHIPPING_REGEX = r'<span class="s-item__shipping s-item__logisticsCost">\n\s{1,100}(\+\$\d{1,}\.\d{1,2})'
        self.LINK_REGEX = (
            r'href="(https:\/\/www\.ebay\.com\/itm\/[\W|\w|\S|\s]{1,100})" tabindex'
        )
        self.url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={self.item_to_search.replace(' ', '+')}&_sacat=0&_ipg=240"

    def run(self) -> None:
        """
        It downloads the html file, parses it, deletes the html file, and emits the data.
        """
        try:
            self.download_html()
            data = self.parse_file()
            os.remove("ebay_scrape_results.txt")
            self.signal.emit(data)
        except Exception as e:
            self.signal.emit(e)

    def download_html(self) -> None:
        """
        This function downloads the HTML of the URL that was passed to the class and writes it to a file
        called ebay_scrape_results.txt
        """
        reqeust = requests.get(self.url)
        soup = BeautifulSoup(reqeust.content, "html5lib")
        with open("ebay_scrape_results.txt", "w", encoding="utf-8") as scrape_results:
            scrape_results.write(soup.prettify())

    def parse_item(self, content: str):
        """
        It takes a string of HTML, finds the title, price, and shipping information, and returns them as
        a tuple.

        Args:
          content (str): str = the html content of the page

        Returns:
          title, price, shipping, link
        """
        title_matches = re.finditer(self.TITLE_REGEX, content, re.MULTILINE)
        price_matches = re.finditer(self.PRICE_REGEX, content, re.MULTILINE)
        shipping_matches = re.finditer(self.SHIPPING_REGEX, content, re.MULTILINE)
        link_matches = re.finditer(self.LINK_REGEX, content, re.MULTILINE)

        title: str = ""
        price: str = ""
        shipping: str = ""
        link: str = ""
        for match in title_matches:
            title = (
                match.group(1)
                .replace("\n", "")
                .replace("  ", "")
                .replace("&amp;", "&")
                .strip()
            )

        for match in price_matches:
            price = match.group(1).strip()

        for match in shipping_matches:
            shipping = f"{match.group(1).strip()} shipping"

        for match in link_matches:
            link_matches = f"{match.group(1).strip()}"

        return title, price, shipping, link

    def parse_file(self) -> dict:
        """
        It opens a file, reads the lines, and then parses the lines to find the title, price,
        shipping cost, and link of each item

        Returns:
          A dictionary of dictionaries.
        """
        with open("ebay_scrape_results.txt", "r", encoding="utf-8") as scrape_results:
            lines = scrape_results.readlines()

        content: str = ""
        found_item: bool = False
        data = {}

        for line in lines:
            if '<li class="s-item s-item__pl-on-bottom s-item--watch-at-corner"' in line:
                found_item = True
            if "</li>" in line and found_item:
                found_item = False
                title, price, shipping, link = self.parse_item(content=content)
                if price != "":
                    data[title] = {"price": price, "shipping": shipping, "url": link}
                content = ""

            if found_item:
                content += line

        return data
