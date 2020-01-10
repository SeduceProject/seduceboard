import logging

import flask_login
from flask import Flask
from blueprints.webapp import webapp_blueprint
from blueprints.webapp_api import webapp_api_blueprint
from blueprints.login import login_blueprint
from blueprints.admin_app import admin_app_blueprint
from flask_profiler import Profiler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from core.config.config_loader import load_config
import os


login_manager = flask_login.LoginManager()

DEBUG = True

# Search the folder containing HTML templates
root_path_candidates = [".", ".."]
root_path = None

for root_path_candidate in root_path_candidates:
    if os.path.exists(f"{root_path_candidate}/templates"):
        root_path = root_path_candidate

if root_path is None:
    raise Exception(f"Could not find root folder among {root_path_candidates}")

# Init Flask application
app = Flask(__name__, root_path=root_path)
app.secret_key = "SeduceFrontendServer"
login_manager.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = load_config().get("db").get("connection_url")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.register_blueprint(webapp_blueprint)
app.register_blueprint(login_blueprint)
app.register_blueprint(webapp_api_blueprint)
app.register_blueprint(admin_app_blueprint)

login_manager.init_app(app)
login_manager.login_view = "login.login"

# Import database models with app context
with app.app_context():
  from database import *

from core.decorators.app import *

if __name__ == "__main__":
    from core.misc import ensure_admin_user_exists

    logging.basicConfig(level=logging.DEBUG)
    # Create DB
    print("Creating database")
    db.create_all()

    # Ensure an admin account is configured
    ensure_admin_user_exists(db)

    # Run front end
    print("Running the \"API/Web\" program")
    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8081, debug=DEBUG, threaded=True)
