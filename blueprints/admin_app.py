import flask
import flask_login
from flask import Blueprint
from flask import render_template
from dateutil import parser
from core.decorators.admin_login_required import admin_login_required

admin_app_blueprint = Blueprint('admin_app', __name__,
                                template_folder='templates')


def validate(date_text):
    try:
        parser.parse(date_text)
    except ValueError:
        return False
    return True


@admin_app_blueprint.route("/admin/continuous_queries")
@admin_login_required
def continuous_queries_management():
    render_template("continuous_queries.html.jinja2")


@admin_app_blueprint.route("/admin/manage_users.html")
@admin_login_required
def manage_users():
    from database import db
    from database import User as DbUser
    db.session.expire_all()
    users = DbUser.query.all()
    return render_template("settings.html.jinja2", users=users)
