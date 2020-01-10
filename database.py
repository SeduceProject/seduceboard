from flask_bcrypt import Bcrypt
from sqlalchemy.ext.hybrid import hybrid_property
from core.finite_state_machine.fsm import user_initial_state, cq_initial_state
from bin.app import app
from sqlalchemy import event
from transitions import Machine
from bin.app import db

bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state = db.Column(db.String(120), default=user_initial_state)
    email = db.Column(db.Text, index=True, unique=True)
    _password = db.Column(db.Text)
    firstname = db.Column(db.Text)
    lastname = db.Column(db.Text)
    url_picture = db.Column(db.Text, nullable=True, default=None)

    email_confirmed = db.Column(db.Boolean, default=False)
    user_authorized = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    email_confirmation_token = db.Column(db.Text, nullable=True, default=None)
    admin_authorization_token = db.Column(db.Text, nullable=True, default=None)
    forgotten_password_token = db.Column(db.Text, nullable=True, default=None)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)


class ContinuousQueryRecomputeJob(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state = db.Column(db.String(120), default=cq_initial_state)

    cq_name = db.Column(db.Text)
    priority = db.Column(db.String(120), default="low")
    time_interval_start = db.Column(db.DateTime, nullable=True)
    time_interval_end = db.Column(db.DateTime, nullable=True)

    last_run_start = db.Column(db.DateTime)
    last_run_end = db.Column(db.DateTime)

    last_execution_time = db.Column(db.BigInteger)


@event.listens_for(User, 'init')
@event.listens_for(User, 'load')
def user_receive_init(obj, *args, **kwargs):
    from core.finite_state_machine.fsm import user_initial_state, user_states, user_transitions
    # when we load data from the DB(via query) we need to set the proper initial state
    initial = obj.state or user_initial_state
    machine = Machine(model=obj, states=user_states, transitions=user_transitions, initial=initial)
    # in case that we need to have machine obj in model obj
    setattr(obj, 'machine', machine)


@event.listens_for(ContinuousQueryRecomputeJob, 'init')
@event.listens_for(ContinuousQueryRecomputeJob, 'load')
def cq_receive_init(obj, *args, **kwargs):
    from core.finite_state_machine.fsm import cq_initial_state, cq_states, cq_transitions
    # when we load data from the DB(via query) we need to set the proper initial state
    initial = obj.state or cq_initial_state
    machine = Machine(model=obj, states=cq_states, transitions=cq_transitions, initial=initial)
    # in case that we need to have machine obj in model obj
    setattr(obj, 'machine', machine)
