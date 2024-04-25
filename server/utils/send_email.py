import json
import smtplib
from datetime import datetime
from email.mime import multipart, text

from utils.custom_print import CustomPrint


def send(body: str, email_addresses: list[str], connected_clients):
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
        email_addresses = ["jaredgrozz@gmail.com", "lynden@pineymfg.com"]

    with open("credentials.json", "r") as credentialsFile:
        credentials = json.load(credentialsFile)
    USERNAME: str = credentials["username"]
    PASSWORD = credentials["password"]
    for email_address in email_addresses:
        msg = multipart.MIMEMultipart()

        msg["From"] = USERNAME
        msg["To"] = email_address
        msg["Subject"] = "Invigo - Sheets to Order"

        msg.attach(text.MIMEText(body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(USERNAME, PASSWORD)
        server.sendmail(USERNAME, email_address, msg.as_string())
        CustomPrint.print(
            f'INFO - Email sent to "{email_address}"',
            connected_clients=connected_clients,
        )


def send_error_log(body: str, connected_clients):
    with open("credentials.json", "r") as credentialsFile:
        credentials = json.load(credentialsFile)
    USERNAME: str = credentials["username"]
    PASSWORD = credentials["password"]
    msg = multipart.MIMEMultipart()

    msg["From"] = USERNAME
    msg["To"] = "jaredgrozz@gmail.com"
    msg["Subject"] = "Invigo - Error Report"
    body = body.replace("\n", "<br>")

    msg.attach(text.MIMEText(body, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(USERNAME, PASSWORD)
    server.sendmail(USERNAME, "jaredgrozz@gmail.com", msg.as_string())
    CustomPrint.print(
        f"INFO - Email sent to jaredgrozz@gmail.com",
        connected_clients=connected_clients,
    )
