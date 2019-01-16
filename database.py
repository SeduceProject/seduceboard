from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from core.finite_state_machine.fsm import user_initial_state
from frontend import app
from sqlalchemy import event
from transitions import Machine

bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


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

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)


@event.listens_for(User, 'init')
@event.listens_for(User, 'load')
def receive_init(obj, *args, **kwargs):
    from core.finite_state_machine.fsm import user_initial_state, user_states, user_transitions
    # when we load data from the DB(via query) we need to set the proper initial state
    initial = obj.state or user_initial_state
    machine = Machine(model=obj, states=user_states, transitions=user_transitions, initial=initial)
    # in case that we need to have machine obj in model obj
    setattr(obj, 'machine', machine)
