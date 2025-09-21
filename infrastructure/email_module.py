# работа с имейлами, сохранением их, включением файлов и т.д

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import Config

def verify_email(to_email, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(Config.SMTP_USER, Config.SMTP_PASS)
        server.send_message(msg)

def send_email_with_attachment(to_email, subject, body, file=None):
    msg = MIMEMultipart()
    msg["From"] = Config.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    # Текст письма
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Прикрепление PDF
    if file and file.filename.endswith(".pdf"):
        pdf = MIMEApplication(file.read(), _subtype="pdf")
        pdf.add_header("Content-Disposition", "attachment", filename=file.filename)
        msg.attach(pdf)

    with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASS)
        server.send_message(msg)



