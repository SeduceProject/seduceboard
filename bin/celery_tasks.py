from flask import Flask
from celery import Celery
from tasks.email import send_confirmation_email, send_authorization_email
from tasks.sensors import detect_unresponsive_temperature_sensors
from tasks.cq_jobs import run_job, wait_job, finish_job


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
    sender.add_periodic_task(20.0, detect_unresponsive_temperature_sensors.s(), name='detect_unresponsive_temperature_sensors')

    sender.add_periodic_task(10.0, run_job.s(), name='run_job')
    sender.add_periodic_task(10.0, wait_job.s(), name='wait_job')
    sender.add_periodic_task(20.0, finish_job.s(), name='finish_job')


if __name__ == "__main__":
    while True:
        send_confirmation_email()
        send_authorization_email()
        detect_unresponsive_temperature_sensors()
        run_job()
        wait_job()
        finish_job()
