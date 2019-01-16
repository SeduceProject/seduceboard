from database import User
from database import db
from core.email.notification import send_confirmation_request
from core.email.notification import send_authorization_request
import celery


@celery.task()
def send_confirmation_email():
    print("Checking users in 'created' state")
    users = User.query.filter_by(state="created").all()
    print(len(users))
    for user in users:

        result = send_confirmation_request(user)

        if result.get("success", False):
            user.email_confirmation_token = result["token"]
            user.email_sent()

            db.session.add(user)
            db.session.commit()


@celery.task()
def send_authorization_email():
    print("Checking users in 'confirmed' state")
    users = User.query.filter_by(state="confirmed").all()
    print(len(users))
    for user in users:
        result = send_authorization_request(user)

        if result.get("success", False):
            user.admin_authorization_token = result["token"]
            user.notify_admin()

            db.session.add(user)
            db.session.commit()
            db.session.commit()
