from flask_mail import Message

from src import app, mail


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)

def send_qr_email(to, subject, body, attachment_path):
    msg = Message(
        subject,
        recipients=[to],
        body=body,
        sender=app.config["MAIL_DEFAULT_SENDER"],
    )
    with app.open_resource(attachment_path) as fp:
        msg.attach(attachment_path, "image/png", fp.read())
    mail.send(msg)