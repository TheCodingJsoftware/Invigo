# Configuring the logging module to write to a file called app.log in a folder called logs.
import logging

logging.basicConfig(
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)
