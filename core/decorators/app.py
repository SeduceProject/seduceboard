from bin.app import login_manager, app


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


@app.context_processor
def inject_dict_for_all_templates():
    from core.config.config_loader import load_config
    api_public_address = load_config().get("api", {}).get("public_address", "localhost:5000")
    return dict(api_public_address=api_public_address)
