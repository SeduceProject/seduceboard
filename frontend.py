import logging

import flask_login
from flask import Flask
from blueprints.webapp import webapp_blueprint
from blueprints.webapp_api import webapp_api_blueprint
from blueprints.login import login_blueprint
from blueprints.admin_app import admin_app_blueprint
from core.misc import prettify_duration as prettify_duration_func


login_manager = flask_login.LoginManager()

DEBUG = True

app = Flask(__name__)
app.secret_key = "SeduceFrontendServer"
login_manager.init_app(app)

app.register_blueprint(webapp_blueprint)
app.register_blueprint(login_blueprint)
app.register_blueprint(webapp_api_blueprint)
app.register_blueprint(admin_app_blueprint)

login_manager.init_app(app)
login_manager.login_view = "login.login"


@login_manager.user_loader
def user_loader(email):
    from core.login.login_management import User
    from database import User as DbUser

    db_user = DbUser.query.filter_by(email=email).first()

    if db_user is not None and db_user.user_authorized:
        user = User()
        user.id = db_user.email
        user.firstname = db_user.firstname
        user.lastname = db_user.lastname
        user.url_picture = db_user.url_picture
        user.is_admin = db_user.is_admin
        user.user_authorized = db_user.user_authorized

        return user

    return None


@login_manager.request_loader
def request_loader(request):
    from core.login.login_management import User, authenticate
    email = request.form.get('email')
    password = request.form.get('email')

    if authenticate(email, password):
        user = User()
        user.id = email
        return User

    return None


@app.teardown_appcontext
def shutdown_session(exception=None):
    from database import db
    db.session.remove()


@app.template_filter()
def prettify_duration(dt, default="just now"):
    prettify_duration_func(dt, default)


@app.context_processor
def inject_dict_for_all_templates():
    from core.config.config_loader import load_config
    api_public_address = load_config().get("api", {}).get("public_address", "localhost:5000")
    return dict(api_public_address=api_public_address)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Create DB
    print("Creating database")
    from database import db
    db.create_all()
    # Ensure an admin account is configured
    from database import User as DbUser
    from core.config.config_loader import load_config
    admin = DbUser.query.filter_by(email=load_config().get("admin").get("user")).first()
    if admin is None:
        admin = DbUser()
        admin.email = load_config().get("admin").get("user")
        admin.firstname = load_config().get("admin").get("firstname")
        admin.lastname = load_config().get("admin").get("lastname")
        admin.password = load_config().get("admin").get("password")
        admin.state = "authorized"
        admin.email_confirmed = True
        admin.user_authorized = True
        admin.is_admin = True
        admin.url_picture = load_config().get("admin").get("url_picture")
        db.session.add(admin)
        db.session.commit()

    # Run front end
    print("Running the \"API/Web\" program")
    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8081, debug=DEBUG, threaded=True)
