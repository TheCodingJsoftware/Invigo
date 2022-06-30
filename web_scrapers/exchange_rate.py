import contextlib
import time

from forex_python.converter import CurrencyRates
from PyQt5.QtCore import QThread, pyqtSignal


class ExchangeRate(QThread):
    """This class is a QThread that scrapes exchange rates from a website and stores them in a dictionary"""

    signal = pyqtSignal(object)

    def __init__(self) -> None:
        """
        The above function is a constructor for the class QThread
        """
        QThread.__init__(self)

    def run(self) -> None:
        """
        It's a function that runs in a thread and emits a signal every 60 seconds
        """
        while True:
            with contextlib.suppress(Exception):
                currency_rates = CurrencyRates()
                self.signal.emit(currency_rates.get_rate("USD", "CAD"))
            time.sleep(60)
