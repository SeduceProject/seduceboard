import flask
from flask import Blueprint
from flask import render_template
import flask_login
from dateutil import parser
from core.decorators.admin_login_required import admin_login_required

login_blueprint = Blueprint('login', __name__,
                            template_folder='templates')


def validate(date_text):
    try:
        parser.parse(date_text)
    except ValueError:
        return False
    return True


@login_blueprint.route('/login', methods=['GET', 'POST'])
@login_blueprint.route('/login?msg=<msg>', methods=['GET', 'POST'])
def login(msg=None):
    if flask.request.method == 'GET':
        next_url = flask.request.args.get("next")
        return render_template("login.html.jinja2", next_url=next_url, msg=msg)
    from core.login.login_management import User, authenticate
    email = flask.request.form['email']
    password = flask.request.form['password']
    next_url = flask.request.form['next_url']
    if authenticate(email, password):
        user = User()
        user.id = email
        is_authenticated = flask_login.login_user(user)
        redirect_url = next_url if (next_url is not None and next_url != "None") else flask.url_for("webapp.index")
        return flask.redirect(redirect_url)

    return flask.redirect(flask.url_for("login.login", msg="You are not authorized to log in"))


def verify_captcha(site_key, secret_key, token, remote_ip=None):
    import requests

    data = {
        "secret": secret_key,
        "response": token,
    }

    if remote_ip is not None:
        data["remoteip"] = remote_ip

    result = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data).json()

    return result.get("success", False)


@login_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    from database import User
    from database import db
    from core.config.config_loader import load_config

    config = load_config()

    recaptcha_site_key = config.get("captcha").get("site_key")
    recaptcha_secret_key = config.get("captcha").get("secret_key")

    if flask.request.method == 'GET':
        next_url = flask.request.args.get("next")
        return render_template("signup.html.jinja2", next_url=next_url, recaptcha_site_key=recaptcha_site_key)
    email = flask.request.form['email']
    firstname = flask.request.form['firstname']
    lastname = flask.request.form['lastname']
    password = flask.request.form['password']
    confirm_password = flask.request.form['confirm_password']
    recaptcha_token = flask.request.form['g-recaptcha-response']

    remote_ip = None

    error = False
    error_msg = ""

    if ".ru" in email:
        remote_ip = flask.request.remote_addr
        error = True
        error_msg = "russian email detected"

    if recaptcha_token == "" or recaptcha_token is None:
        error = True
        error_msg = "no recaptcha token provided"

    if not verify_captcha(recaptcha_site_key, recaptcha_secret_key, recaptcha_token, remote_ip):
        error = True
        error_msg = "invalid recaptcha token"

    if not error and password == confirm_password:
        user = User()
        user.email = email
        user.firstname = firstname
        user.lastname = lastname
        # The password is ciphered and salted in the database.py file
        user.password = password

        db.session.add(user)
        db.session.commit()

        redirect_url = flask.url_for("login.confirmation_account_creation")
        return flask.redirect(redirect_url)
    else:
        print("SPAM: %s (%s)" % (remote_ip, error_msg))

    return 'Bad login'


@login_blueprint.route('/request_reset_password', methods=['GET', 'POST'])
def request_reset_password():
    from database import User
    from core.email.notification import send_reset_password_link
    from database import db
    if flask.request.method == 'GET':
        next_url = flask.request.args.get("next")
        return render_template("request_reset_password.html.jinja2", next_url=next_url, msg="")
    email = flask.request.form['email']
    if email is not None and email != "":
        user = User.query.filter_by(email=email).first()

        if user is None:
            return render_template("request_reset_password.html.jinja2", msg="No user is registered with this email")
        else:

            response = send_reset_password_link(user)
            reset_password_token = response.get("token")
            user.forgotten_password_token = reset_password_token

            db.session.add(user)
            db.session.commit()

            redirect_url = flask.url_for("login.login", msg="We just sent you an email to help you reset your password!")
    else:
        redirect_url = flask.url_for("login.login")
    return flask.redirect(redirect_url)


@login_blueprint.route('/reset_password/token/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from database import User
    from core.email.notification import send_reset_password_link
    from database import db
    if flask.request.method == 'GET':
        return render_template("reset_password.html.jinja2", msg="", token=token)
    password1 = flask.request.form['password1']
    password2 = flask.request.form['password2']
    if password1 is not None and password1 != "" and password1 == password2:
        user = User.query.filter_by(forgotten_password_token=token).first()

        if user is None:
            redirect_url = flask.url_for("login.login", msg="The password request is invalid (bad token)")
        else:
            user.password = password1
            user.forgotten_password_token = ""

            db.session.add(user)
            db.session.commit()

            redirect_url = flask.url_for("login.login", msg="We just updated your password!")
    else:
        return render_template("reset_password.html.jinja2", msg="Passwords don't match!", token=token)
    return flask.redirect(redirect_url)


@login_blueprint.route('/confirmation_account_creation')
def confirmation_account_creation():
    return render_template("confirmation_account_creation.html.jinja2")


@login_blueprint.route('/confirmation_account_confirmation')
def confirmation_account_confirmation():
    return render_template("confirmation_account_confirmation.html.jinja2")


@login_blueprint.route('/confirm_email/token/<token>')
def confirm_email(token):
    from database import User
    from database import db
    db.session.expire_all()
    user_candidate = User.query.filter_by(email_confirmation_token=token).first()

    if user_candidate is not None:
        if user_candidate.state == "waiting_confirmation_email":
            user_candidate.confirm_email()
            user_candidate.email_confirmed = True
            db.session.add(user_candidate)
            db.session.commit()
        return flask.redirect(flask.url_for("login.confirmation_account_confirmation"))

    return "Bad request: could not find the given token '%s'" % (token)


@login_blueprint.route('/approve_user/token/<token>')
@admin_login_required
def approve_user(token):
    from database import User
    from core.email.notification import send_authorization_confirmation
    from database import db
    db.session.expire_all()
    user_candidate = User.query.filter_by(admin_authorization_token=token).first()

    if user_candidate is not None:
        user_candidate.approve()
        user_candidate.user_authorized = True
        db.session.add(user_candidate)
        db.session.commit()
        send_authorization_confirmation(user_candidate)
        return flask.redirect(flask.url_for("admin_app.manage_users"))

    return "Bad request: could not approve a user with the given token '%s'" % (token)


@login_blueprint.route('/disapprove_user/token/<token>')
@admin_login_required
def disapprove_user(token):
    from database import User
    from database import db
    user_candidate = User.query.filter_by(admin_authorization_token=token).first()

    if user_candidate is not None:
        user_candidate.disapprove()
        user_candidate.user_authorized = False
        db.session.add(user_candidate)
        db.session.commit()
        return flask.redirect(flask.url_for("admin_app.manage_users"))

    return "Bad request: could not disapprove find givent token '%s'" % (token)


@login_blueprint.route('/promote_user/<user_id>')
@admin_login_required
def promote_user(user_id):
    from database import User
    from database import db
    db.session.expire_all()
    user_candidate = User.query.filter_by(id=user_id).first()

    if user_candidate is not None:
        user_candidate.is_admin = True
        db.session.add(user_candidate)
        db.session.commit()
        return flask.redirect(flask.url_for("admin_app.manage_users"))
    return "Bad request: could not promote a user with given id '%s'" % (user_id)


@login_blueprint.route('/demote_user/<user_id>')
@admin_login_required
def demote_user(user_id):
    from database import User
    from database import db
    db.session.expire_all()
    user_candidate = User.query.filter_by(id=user_id).first()

    if user_candidate is not None:
        user_candidate.is_admin = False
        db.session.add(user_candidate)
        db.session.commit()
        return flask.redirect(flask.url_for("admin_app.manage_users"))
    return "Bad request: could not demote a user with given id '%s'" % (user_id)


@login_blueprint.route('/authorize_user/<user_id>')
@admin_login_required
def authorize_user(user_id):
    from database import User
    from database import db
    db.session.expire_all()
    user_candidate = User.query.filter_by(id=user_id).first()

    if user_candidate is not None:
        if user_candidate.state == "waiting_authorization":
            user_candidate.approve()
        elif user_candidate.state == "unauthorized":
            user_candidate.reauthorize()
        user_candidate.user_authorized = True
        db.session.add(user_candidate)
        db.session.commit()
        return flask.redirect(flask.url_for("admin_app.manage_users"))
    return "Bad request: could not authorize a user with given id '%s'" % (user_id)


@login_blueprint.route('/deauthorize_user/<user_id>')
@admin_login_required
def deauthorize_user(user_id):
    from database import User
    from database import db
    db.session.expire_all()
    user_candidate = User.query.filter_by(id=user_id).first()

    if user_candidate is not None:
        user_candidate.deauthorize()
        user_candidate.user_authorized = False
        db.session.add(user_candidate)
        db.session.commit()
        return flask.redirect(flask.url_for("admin_app.manage_users"))
    return "Bad request: could not deauthorize a user with given id '%s'" % (user_id)


@login_blueprint.route('/delete_user/<user_id>')
@admin_login_required
def delete_user(user_id):
    from database import User
    from database import db
    db.session.expire_all()
    user_candidate = User.query.filter_by(id=user_id).first()

    if user_candidate is not None:
        db.session.delete(user_candidate)
        db.session.commit()
        return flask.redirect(flask.url_for("admin_app.manage_users"))
    return "Bad request: could not delete a user with given id '%s'" % (user_id)


@login_blueprint.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("webapp.index"))
