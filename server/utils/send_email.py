import smtplib
from email.mime import multipart, text

import ujson as json


def send(body: str, email_addresses: list[str] = None):
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

    with open("credentials.json", "r") as credentialsFile:
        credentials = json.load(credentialsFile)
    USERNAME: str = credentials["username"]
    PASSWORD = credentials["password"]
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
