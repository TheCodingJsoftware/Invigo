import smtplib
from datetime import datetime
from email.mime import multipart, text


def send(body: str, email_addresses: list[str] = None):
# `price_of_steel_inventory` is creating an instance of the `JsonFile` class and initializing it with
# the file path "server/data/inventory - Price of Steel.json". This suggests that the file contains
# data related to the inventory and prices of steel.
    """
    This function sends an email with a specified body to a list of email addresses using Gmail's SMTP
    server.

    Args:
      body (str): The message body that will be sent in the email.
      email_addresses (list[str]): A list of email addresses to which the email will be sent. If this
    parameter is not provided, the email will be sent to the default email addresses specified in the
    function.
    """
    if email_addresses is None:
        email_addresses = ['jaredgrozz@gmail.com', 'lynden@pineymfg.com']
    USERNAME: str = 'jaredgrozz@gmail.com'
    PASSWORD = 'iadiqglipqjhdgvq'
    for email_address in email_addresses:

        msg = multipart.MIMEMultipart()

        msg['From'] = USERNAME
        msg['To'] = email_address
        msg['Subject'] = 'Inventory Manager Sheets to Order'

        msg.attach(text.MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(USERNAME, PASSWORD)
        server.sendmail(USERNAME, email_address, msg.as_string())
        print(f'send to {email_address}')
