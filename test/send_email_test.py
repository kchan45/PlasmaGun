import email
import smtplib
import ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


subject = "Test email with attachment"
body = "sending a test email from python with an attachment"
sender_email = "gremipg2022@gmail.com"
password = "yozpzhkdunctesnz"

receiver_email = input("Enter email to send data: \n")


# create the multipart message and set headers
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message["Bcc"] = receiver_email

# attach body to email
message.attach(MIMEText(body, "plain"))

csv_filename = "test.csv"

with open(csv_filename, 'rb') as file:
    message.attach(MIMEApplication(file.read(), Name="test.csv"))


context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message.as_string())
