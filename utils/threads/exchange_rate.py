import contextlib
import time

from forex_python.converter import CurrencyRates
from PyQt6.QtCore import QThread, pyqtSignal


class ExchangeRate(QThread):
    signal = pyqtSignal(object)

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        while True:
            with contextlib.suppress(Exception):
                currency_rates = CurrencyRates()
                self.signal.emit(currency_rates.get_rate("USD", "CAD"))
            time.sleep(60)
