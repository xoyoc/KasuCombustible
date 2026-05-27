import os
from pathlib import Path
from sendgrid import SendGridAPIClient, SendGridException
from sendgrid.helpers.mail import Mail, Email, To, Content

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

def sendMail(email, titulo, contenido):
    from_email = Email("combustible@loginco.com")
    to_email = To(email)
    subject = titulo
    content = Content("text/html", contenido)
    mail = Mail(from_email, to_email, subject, content)
    try:
        sg = SendGridAPIClient(api_key=env.str('SENDGRID_API_KEY'))
        response = sg.client.mail.send.post(request_body=mail.get())
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except SendGridException as e:
        print(e.message)

