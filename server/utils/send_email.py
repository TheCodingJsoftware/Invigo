import smtplib
from email.mime import multipart
from email.mime import text
from datetime import datetime
from json_file import JsonFile

price_of_steel_inventory = JsonFile(file_name="server/data/inventory - Price of Steel.json")
# , 'jordan@pineymfg.com', 'lynden@pineymfg.com'
def send(body: str, email_addresses: list[str] = ['jaredgrozz@gmail.com', 'lynden@pineymfg.com']):
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
