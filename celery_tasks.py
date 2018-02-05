from flask import Flask
from celery import Celery
from database import User
from database import db
from core.email.notification import send_confirmation_request, send_authorization_request


def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://127.0.0.1:6379',
    CELERY_RESULT_BACKEND='redis://127.0.0.1:6379'
)
celery = make_celery(flask_app)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, send_confirmation_email.s(), name='send_confirmation_email')
    sender.add_periodic_task(10.0, send_authorization_email.s(), name='send_authorization_email')
    sender.add_periodic_task(120.0, detect_unresponsive_temperature_sensors.s(), name='detect_unresponsive_temperature_sensors')


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


@celery.task()
def detect_unresponsive_temperature_sensors():
    print("Detecting unresponsive temperature detectors")
    from core.data.sensors import get_sensors_arrays_with_children
    from core.data.db import db_last_sensors_updates
    import time
    from dateutil import parser
    from core.data.db_redis import redis_increment_sensor_error_count

    last_updates = db_last_sensors_updates()
    sensors_arrays_with_children = get_sensors_arrays_with_children()
    now_time = time.time()

    for sensors_array in sensors_arrays_with_children:
        for child in sensors_array["children"]:
            child_last_update = filter(lambda x: x["sensor"] == child["name"], last_updates)
            if len(child_last_update) > 0:
                last_update_since_epoch = int(time.mktime(parser.parse(child_last_update[0]["time"]).timetuple())) - time.timezone
                time_since_last_update_secs = now_time - last_update_since_epoch

                if time_since_last_update_secs > 60:
                    redis_increment_sensor_error_count(child.get("name"))


if __name__ == "__main__":
    send_confirmation_email()
    send_authorization_email()
    detect_unresponsive_temperature_sensors()
