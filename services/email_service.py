from flask_mail import Message
from extensions import mail


def send_email(subject, recipients, body):
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body
        )

        mail.send(msg)

        return True

    except Exception as e:
        print(f"Email sending failed: {e}")
        return False