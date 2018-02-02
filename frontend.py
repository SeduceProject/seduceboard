import logging

import flask_login
from dateutil import parser
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
import flask
from core.decorators.admin_login_required import admin_login_required

login_manager = flask_login.LoginManager()

DEBUG = True

app = Flask(__name__)
app.secret_key = "SeduceFrontendServer"
login_manager.init_app(app)
login_manager.login_view = "login"


def validate(date_text):
    try:
        parser.parse(date_text)
    except ValueError:
        return False
    return True


@login_manager.user_loader
def user_loader(email):
    from login_management import User
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
    from login_management import User, authenticate
    email = request.form.get('email')
    password = request.form.get('email')

    if authenticate(email, password):
        user = User()
        user.id = email
        return User

    return None


@app.route('/login', methods=['GET', 'POST'])
@app.route('/login?msg=<msg>', methods=['GET', 'POST'])
def login(msg=None):
    if flask.request.method == 'GET':
        next_url = flask.request.args.get("next")
        return render_template("login.html", next_url=next_url, msg=msg)
    from login_management import User, authenticate
    email = flask.request.form['email']
    password = flask.request.form['password']
    next_url = flask.request.form['next_url']
    if authenticate(email, password):
        user = User()
        user.id = email
        is_authenticated = flask_login.login_user(user)
        redirect_url = next_url if (next_url is not None and next_url != "None") else flask.url_for("index")
        return flask.redirect(redirect_url)

    return flask.redirect(flask.url_for("login", msg="You are not authorized to log in"))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    from database import User
    if flask.request.method == 'GET':
        next_url = flask.request.args.get("next")
        return render_template("signup.html", next_url=next_url)
    email = flask.request.form['email']
    firstname = flask.request.form['firstname']
    lastname = flask.request.form['lastname']
    password = flask.request.form['password']
    confirm_password = flask.request.form['confirm_password']
    if password == confirm_password:
        user = User()
        user.email = email
        user.firstname = firstname
        user.lastname = lastname
        # The password is ciphered and salted in the database.py file
        user.password = password

        db.session.add(user)
        db.session.commit()

        redirect_url = flask.url_for("confirmation_account_creation")
        return flask.redirect(redirect_url)

    return 'Bad login'


@app.route('/confirmation_account_creation')
def confirmation_account_creation():
    return render_template("confirmation_account_creation.html")


@app.route('/confirmation_account_confirmation')
def confirmation_account_confirmation():
    return render_template("confirmation_account_confirmation.html")


@app.route('/confirm_email/token/<token>')
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
        return flask.redirect(flask.url_for("confirmation_account_confirmation"))

    return "Bad request: could not find the given token '%s'" % (token)


@app.route('/approve_user/token/<token>')
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
        return flask.redirect(flask.url_for("settings"))

    return "Bad request: could not the find given token '%s'" % (token)


@app.route('/disapprove_user/token/<token>')
def disapprove_user(token):
    from database import User
    user_candidate = User.query.filter_by(admin_authorization_token=token).first()

    if user_candidate is not None:
        user_candidate.disapprove()
        user_candidate.user_authorized = False
        db.session.add(user_candidate)
        db.session.commit()
        return flask.redirect(flask.url_for("settings"))

    return "Bad request: could not find givent token '%s'" % (token)


@app.route('/promote_user/<user_id>')
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
        return flask.redirect(flask.url_for("settings"))
    return "Bad request: could not a user with given id '%s'" % (user_id)


@app.route('/demote_user/<user_id>')
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
        return flask.redirect(flask.url_for("settings"))
    return "Bad request: could not a user with given id '%s'" % (user_id)


@app.route('/authorize_user/<user_id>')
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
        return flask.redirect(flask.url_for("settings"))
    return "Bad request: could not a user with given id '%s'" % (user_id)


@app.route('/deauthorize_user/<user_id>')
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
        return flask.redirect(flask.url_for("settings"))
    return "Bad request: could not a user with given id '%s'" % (user_id)


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("index"))


@app.route("/sensor_data/<sensor_name>")
def sensor_data(sensor_name):
    from core.data.db import db_sensor_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date
        else:
            raise Exception("Invalid 'start_date' parameter: %s" % (start_date))

    end_date = None
    if "end_date" in request.args:
        end_date = request.args["end_date"]
        if validate(end_date):
            end_date = "'%s'" % end_date
        else:
            raise Exception("Invalid 'end_date' parameter: %s" % (end_date))

    zoom_ui = "zoom_ui" in request.args

    _sensor_data = db_sensor_data(sensor_name, start_date, end_date, zoom_ui)
    return jsonify(_sensor_data)


@app.route("/sensors")
@app.route("/sensors/all")
@app.route("/sensors/<sensor_type>")
def sensors(sensor_type=None):
    from core.data.db import db_sensors
    _sensors = db_sensors(sensor_type=sensor_type)
    return jsonify(_sensors)


@app.route("/sensors_types")
@app.route("/sensor_types")
def sensor_types():
    from core.data.db import db_sensor_types

    _sensor_types = db_sensor_types()
    return jsonify(_sensor_types)


@app.route("/multitree/root")
def multitree_root_nodes():
    from core.data.multitree import get_root_nodes
    return jsonify(get_root_nodes())


@app.route("/multitree/query/tree/<node_id>")
def multitree_tree_query(node_id):
    from core.data.multitree import get_node_by_id
    from core.data.multitree import get_tree
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        tree = get_tree(starting_node, False)
        return jsonify(tree)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@app.route("/multitree/query/sensors/<node_id>")
def multitree_sensors_query(node_id):
    from core.data.multitree import get_node_by_id
    from core.data.multitree import get_sensors_tree
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        sensors = get_sensors_tree(starting_node)
        return jsonify(sensors)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@app.route("/multitree/query/sensors/<node_id>/data")
def multitree_sensors_data_query(node_id):
    from core.data.multitree import get_node_by_id
    from core.data.multitree import get_sensors_tree
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        sensors = get_sensors_tree(starting_node)
        return jsonify(sensors)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@app.route("/locations")
def locations():
    from core.data.db import db_locations

    _locations = db_locations()
    return jsonify(_locations)


@app.route("/sensor_data/<sensor_name>/aggregated")
@app.route("/sensor_data/<sensor_name>/aggregated/<how>")
def aggregated_sensor_data(sensor_name, how="daily"):
    from core.data.db import db_aggregated_sensor_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _aggregated_sensor_data = db_aggregated_sensor_data(sensor_name=sensor_name, start_date=start_date, how=how)
    return jsonify(_aggregated_sensor_data)


@app.route("/multitree_sensor_data/<sensor_name>/aggregated")
@app.route("/multitree_sensor_data/<sensor_name>/aggregated/<how>")
def aggregated_multitree_sensor_data(sensor_name, how="minutely"):
    from core.data.db import db_aggregated_multitree_sensor_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    end_date = None
    if "end_date" in request.args:
        end_date = request.args["end_date"]
        if validate(end_date):
            end_date = "'%s'" % end_date

    _aggregated_sensor_data = db_aggregated_multitree_sensor_data(sensor_name=sensor_name, start_date=start_date, end_date=end_date, how=how)
    return jsonify(_aggregated_sensor_data)


@app.route("/data/<how>")
def datainfo(how="daily"):
    from core.data.db import db_datainfo

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _datainfo = db_datainfo(start_date=start_date, how=how)
    return jsonify(_datainfo)


@app.route("/data/hardcoded/<sensor_type>/<how>")
def wattmeters_data(sensor_type, how="daily"):
    from core.data.db import db_wattmeters_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _wattmeters_data = db_wattmeters_data(sensor_type=sensor_type, start_date=start_date, how=how)
    return jsonify(_wattmeters_data)


@app.route("/ui/data/navigation/<sensor_type>/<how>")
def get_navigation_data(sensor_type, how="daily"):
    from core.data.db import db_get_navigation_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _navigation_data = db_get_navigation_data(sensor_type, start_date, how)
    return jsonify(_navigation_data)


@app.route("/monitoring/queries")
def queries():
    from core.data.db import db_get_running_queries

    queries = db_get_running_queries()
    return jsonify(queries)


@app.route("/")
@flask_login.login_required
def index():
    from core.data.multitree import get_node_by_id, _get_last_node_consumption
    from core.data.db import db_last_temperature_mean
    datacenter_node = get_node_by_id("datacenter")
    cluster_hardware = get_node_by_id("hardware_cluster")
    datacenter_consumption = _get_last_node_consumption(datacenter_node)
    cluster_hardware_consumption = _get_last_node_consumption(cluster_hardware)

    pue_ratio = datacenter_consumption / cluster_hardware_consumption

    last_temperature_mean = db_last_temperature_mean()

    return render_template("index.html",
                           pue_ratio=pue_ratio,
                           datacenter_consumption=datacenter_consumption,
                           cluster_hardware_consumption=cluster_hardware_consumption,
                           last_temperature_mean=last_temperature_mean)


@app.route("/settings.html")
@admin_login_required
def settings():
    from database import db
    from database import User as DbUser
    db.session.expire_all()
    users = DbUser.query.all()
    return render_template("settings.html", users=users)


@app.route("/wattmeters_all.html")
@flask_login.login_required
def wattmeters():
    return render_template("graphics/wattmeters_all.html")


@app.route("/wattmeters_aggregated.html")
@flask_login.login_required
def wattmeters_aggregated():
    return render_template("graphics/wattmeters_aggregated.html")


@app.route("/socomecs_aggregated.html")
@flask_login.login_required
def socomecs_aggregated():
    return render_template("graphics/socomecs_aggregated.html")


@app.route("/last_sensors_updates")
def last_sensors_updates():
    from core.data.db import db_last_sensors_updates
    last_updates = db_last_sensors_updates()
    return jsonify(last_updates)


intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
    )


def _display_time(seconds, granularity=2):
    if seconds < 1.0:
        return "now"

    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


@app.route("/sensors.html")
@flask_login.login_required
def web_sensors():
    from core.data.sensors import get_sensors_arrays_with_children
    from core.data.db import db_last_sensors_updates
    import time

    last_updates = db_last_sensors_updates()
    sensors_arrays_with_children = get_sensors_arrays_with_children()
    now_time = time.time()
    
    for sensors_array in sensors_arrays_with_children:
        for child in sensors_array["children"]:
            child_last_update = filter(lambda x: x["sensor"] == child["name"], last_updates)
            if len(child_last_update) > 0:
                last_update_since_epoch = int(time.mktime(parser.parse(child_last_update[0]["time"]).timetuple())) - time.timezone
                time_since_last_update_secs = now_time - last_update_since_epoch
                displayed_time_text = _display_time(time_since_last_update_secs)
                child_last_update[0]["nice_last_udpate_text"] = displayed_time_text
                child["last_update"] = child_last_update[0]
            else:
                child["last_update"] = None
    return render_template("sensors.html", last_updates=last_updates, sensors_arrays_with_children=sensors_arrays_with_children)


@app.route("/measurements/wattmeters.html")
@flask_login.login_required
def measurements_wattmeters():
    return render_template("measurements_wattmeters.html")


@app.route("/measurements/thermometers.html")
@flask_login.login_required
def measurements_thermometers():
    return render_template("measurements_thermometers.html")


@app.route("/measurements/socomecs.html")
@flask_login.login_required
def measurements_socomecs():
    return render_template("measurements_socomecs.html")


@app.route("/weighted_tree_consumption_data")
@flask_login.login_required
def weighted_tree_consumption_data():
    from core.data.multitree import get_datacenter_weighted_tree_consumption_data
    return jsonify(get_datacenter_weighted_tree_consumption_data())


@app.route("/weighted_tree_consumption")
@flask_login.login_required
def weighted_tree_consumption():
    return render_template("weighted_tree_consumption.html")


@app.route("/rack_temperature/sensors")
@flask_login.login_required
def rack_temperature_sensors():
    from core.config.room_config import get_temperature_sensors_infrastructure
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()

    return jsonify(temperature_sensors_infrastructure)


@app.route("/rack_temperature/sensors/last_values")
@flask_login.login_required
def rack_temperature_sensors_last_values():
    from core.config.room_config import get_temperature_sensors_infrastructure
    from core.data.db import db_last_temperature_values
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()
    last_temperature_values = db_last_temperature_values()

    for sensor_array_name in temperature_sensors_infrastructure:
        sensor_array = temperature_sensors_infrastructure[sensor_array_name]
        sensor_array["last_temperatures"] = \
                [x for x in last_temperature_values if x["sensor"] in sensor_array["sensors"]]

    return jsonify(temperature_sensors_infrastructure)


@app.route("/rack_temperature_overview.html")
@flask_login.login_required
def rack_temperature_overview():
    from core.config.room_config import get_temperature_sensors_infrastructure
    from core.data.db import db_last_temperature_values
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()
    last_temperature_values = db_last_temperature_values()

    for sensor_array_name in temperature_sensors_infrastructure:
        sensor_array = temperature_sensors_infrastructure[sensor_array_name]
        sensor_array["last_temperatures"] = \
            [x for x in last_temperature_values if x["sensor"] in sensor_array["sensors"]]

    return render_template("rack_temperature_overview.html",
                           temperature_sensors_infrastructure=temperature_sensors_infrastructure)


@app.route("/rack_temperature_errors/sensors/last_values")
@flask_login.login_required
def rack_temperature_sensors_errors_last_values():
    from core.config.room_config import get_temperature_sensors_infrastructure
    from core.data.db_redis import redis_get_sensors_data
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()

    temperature_errors_data = redis_get_sensors_data()

    for sensor_array_name in temperature_sensors_infrastructure:
        sensor_array = temperature_sensors_infrastructure[sensor_array_name]
        last_errors = []
        for sensor_name in sensor_array["sensors"]:
            if sensor_name in temperature_errors_data and "error_count" in temperature_errors_data[sensor_name]:
                error_count = temperature_errors_data[sensor_name]["error_count"]
            else:
                error_count = 0
            last_errors += [{"sensor": sensor_name, "last_value": error_count}]

        sensor_array["last_temperatures"] = last_errors

    return jsonify(temperature_sensors_infrastructure)


@app.route("/rack_temperature_overview.html/errors/increment/<sensor_name>")
@flask_login.login_required
def rack_temperature_errors_incr(sensor_name):
    from core.data.db_redis import redis_get_sensors_data
    from core.data.db_redis import redis_increment_sensor_error_count

    redis_increment_sensor_error_count(sensor_name)
    sensors_data = redis_get_sensors_data()

    return jsonify(sensors_data)


@app.route("/rack_temperature_overview.html/errors")
@flask_login.login_required
def rack_temperature_errors_overview():
    from core.config.room_config import get_temperature_sensors_infrastructure
    from core.data.db_redis import redis_get_sensors_data
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()

    temperature_errors_data = redis_get_sensors_data()

    for sensor_array_name in temperature_sensors_infrastructure:
        sensor_array = temperature_sensors_infrastructure[sensor_array_name]
        last_errors = []
        for sensor_name in sensor_array["sensors"]:
            if sensor_name in temperature_errors_data and "error_count" in temperature_errors_data[sensor_name]:
                error_count = temperature_errors_data[sensor_name]["error_count"]
            else:
                error_count = 0
            last_errors += [{"sensor": sensor_name, "last_value": error_count}]

        sensor_array["last_temperatures"] = last_errors

    return render_template("rack_temperature_errors_overview.html",
                           temperature_sensors_infrastructure=temperature_sensors_infrastructure)


@app.route("/room_overview.html")
@app.route("/room_overview.html/<sensors_array_name>")
@app.route("/room_overview.html/<sensors_array_name>/<selected_sensor>")
@app.route("/room_overview.html/by_selected/<selected_sensor>")
@flask_login.login_required
def room_overview(sensors_array_name=None, selected_sensor=None):
    from core.data.sensors import get_sensors_arrays, get_sensor_by_name
    sensors_arrays = get_sensors_arrays()
    sensors_array = None
    sensor = None
    if selected_sensor is not None:
        sensor = get_sensor_by_name(selected_sensor)
        if sensors_array_name is None:
            sensors_array_name = sensor["parent"]
    if sensors_array_name is not None:
        sensors_array = get_sensor_by_name(sensors_array_name)
    return render_template("room_overview.html",
                           sensors_arrays=sensors_arrays,
                           selected_sensors_array=sensors_array,
                           selected_sensor=sensor)


@app.route("/sensors_array.html/<sensors_array_name>")
@app.route("/sensors_array.html/<sensors_array_name>/<selected_sensor>")
@flask_login.login_required
def sensors_array(sensors_array_name, selected_sensor=None):
    from core.data.sensors import get_sensors_in_sensor_array
    sensors = map(lambda x: x["name"], get_sensors_in_sensor_array(sensors_array_name))
    return render_template("sensors_array.html",
                           sensors=sensors,
                           sensors_array_name=sensors_array_name,
                           selected_sensor=selected_sensor)


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
