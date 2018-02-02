from core.config.email import get_email_configuration
import smtplib
import random
import string
from database import db

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TOKEN_LENGTH = 50


def send_confirmation_request(user):
    email_configuration = get_email_configuration()

    token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(TOKEN_LENGTH))

    fromaddr = email_configuration.get("email")
    toaddr = user.email

    msg = MIMEMultipart()

    msg['From'] = email_configuration.get("email")
    msg['To'] = toaddr
    msg['Subject'] = "Please confirm your email"

    body = """Hello %s,

Thanks for creating an account on the Seduce system.

In order to proceed with your account creation, please confirm your email by browsing on the following link:
http://localhost:8081/confirm_email/token/%s

Best Regards,
Seduce administrators
""" % (user.firstname, token)

    msg.attach(MIMEText(body, 'plain'))

    smtpserver = smtplib.SMTP(email_configuration.get("smtp_server_url"), email_configuration.get("smtp_server_port"))
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(fromaddr, email_configuration.get("password"))
    text = msg.as_string()
    smtpserver.sendmail(fromaddr, toaddr, text)
    smtpserver.quit()

    return {
        "success": True,
        "token": token
    }


def send_authorization_request(user):
    email_configuration = get_email_configuration()

    token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(TOKEN_LENGTH))

    fromaddr = email_configuration.get("email")
    toaddr = fromaddr

    msg = MIMEMultipart()

    msg['From'] = email_configuration.get("email")
    msg['To'] = toaddr
    msg['Subject'] = "A user requested a new account"

    body = """Hello,

A user has made a request for an account creation. As he has successfully confirmed his email,
you now have to review his request in order to decide the request is accepted.

Here are the details of the request:
email: %s
firstname: %s
lastname: %s

In the case you approve his account, he we will get access to the Seduce system.
Do you approve the request?

Yes, I approve the request:
http://localhost:8081/approve_user/token/%s

No, I disapprove the request:
http://localhost:8081/disapprove_user/token/%s


Thanks for taking the time to review this request.

Best Regards,
Seduce system
""" % (user.email, user.firstname, user.lastname, token, token)

    msg.attach(MIMEText(body, 'plain'))

    smtpserver = smtplib.SMTP(email_configuration.get("smtp_server_url"), email_configuration.get("smtp_server_port"))
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(fromaddr, email_configuration.get("password"))
    text = msg.as_string()
    smtpserver.sendmail(fromaddr, toaddr, text)
    smtpserver.quit()

    return {
        "success": True,
        "token": token
    }


def send_authorization_confirmation(user):
    email_configuration = get_email_configuration()

    fromaddr = email_configuration.get("email")
    toaddr = user.email

    msg = MIMEMultipart()

    msg['From'] = email_configuration.get("email")
    msg['To'] = toaddr
    msg['Subject'] = "You account has been approved"

    body = """Hello %s,

You account has been approved by an admin, in consequence you can now log in:
http://localhost:8081/login

Best Regards,
Seduce system
""" % user.firstname

    msg.attach(MIMEText(body, 'plain'))

    smtpserver = smtplib.SMTP(email_configuration.get("smtp_server_url"), email_configuration.get("smtp_server_port"))
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(fromaddr, email_configuration.get("password"))
    text = msg.as_string()
    smtpserver.sendmail(fromaddr, toaddr, text)
    smtpserver.quit()

    return {
        "success": True,
    }