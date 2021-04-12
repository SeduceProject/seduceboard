from flask import Blueprint
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from dateutil import parser
from core.decorators.admin_login_required import admin_login_required
from core.continuous_queries.continuous_queries import list_continuous_queries, get_continuous_query_by_name
from core.continuous_queries.continuous_queries import list_expected_cqs_names
import datetime
import time
from core.data.influx import db_oldest_point_in_serie

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
    # Print password to send it to users
    #from database import bcrypt
    #print(bcrypt.generate_password_hash("seducedashboard2021"))
    cqs = list_continuous_queries()
    return render_template("continuous_queries.html.jinja2", continuous_queries=cqs)


@admin_app_blueprint.route("/admin/continuous_queries/<query_name>")
@admin_login_required
def continuous_query(query_name):
    cqs = get_continuous_query_by_name(query_name)
    return render_template("continuous_query.html.jinja2", continuous_query=cqs)


@admin_app_blueprint.route("/admin/continuous_queries/diagnostic")
@admin_login_required
def continuous_query_diagnostic():
    existing_cqs = [cq.get("name") for cq in list_continuous_queries()]
    expected_cqs = list_expected_cqs_names()

    missing_cqs = [cq for cq in expected_cqs if cq not in existing_cqs]
    unknown_cqs = [cq for cq in existing_cqs if cq not in expected_cqs]

    return render_template("continuous_query_diagnostic.html.jinja2", missing_cqs=missing_cqs, unknown_cqs=unknown_cqs)


@admin_app_blueprint.route("/admin/continuous_queries/production/recreate")
@admin_login_required
def continuous_query_recreate_production_queries():
    from core.data.cq_aggregates import cq_production_recreate_all
    cq_production_recreate_all(recreate_all=True)
    return redirect(url_for("admin_app.continuous_query_diagnostic"))


@admin_app_blueprint.route("/admin/continuous_queries/consumption/recreate")
@admin_login_required
def continuous_query_recreate_consumption_queries():
    from core.data.cq_aggregates import cq_multitree_recreate_all
    cq_multitree_recreate_all(recreate_all=True)
    return redirect(url_for("admin_app.continuous_query_diagnostic"))


@admin_app_blueprint.route("/admin/continuous_queries/prepare_rerun")
@admin_login_required
def prepare_rerun_continuous_query():
    existing_cqs = [cq.get("name") for cq in list_continuous_queries()]
    return render_template("prepare_rerun_continuous_query.jinja2", existing_cqs=existing_cqs)


@admin_app_blueprint.route("/admin/continuous_queries/process_rerun", methods=["POST"])
@admin_login_required
def process_rerun_continuous_query():
    from database import ContinuousQueryRecomputeJob
    from database import db
    selected_cqs = request.form.getlist('selected_cqs')

    # For each serie, detect the oldest know point in the InfluxDB serie
    oldest_points_series = {}
    high_priority_cqs = []
    for cq_name in selected_cqs:
        cq = get_continuous_query_by_name(cq_name)
        if "influx_sensor_id" in cq:
            influx_serie_name = cq.get("influx_sensor_id")
            sensor_id = cq.get("sensor_id")
            oldest_points_series[sensor_id] = db_oldest_point_in_serie(influx_serie_name)
            high_priority_cqs += [cq_name]
    # Create a recomputation job for each serie
    for cq_name in selected_cqs:
        cq = get_continuous_query_by_name(cq_name)
        sensor_id = cq.get("sensor_id")
        if sensor_id in oldest_points_series:
            cq = get_continuous_query_by_name(cq_name)
            new_recomputation_job = ContinuousQueryRecomputeJob()
            new_recomputation_job.cq_name = cq_name
            start_date = datetime.datetime.strptime(oldest_points_series.get(sensor_id).get("time"), '%Y-%m-%dT%H:%M:%SZ')
            new_recomputation_job.time_interval_start = start_date
            new_recomputation_job.time_interval_end = datetime.datetime.now()
            new_recomputation_job.priority = "high" if cq_name in high_priority_cqs else "low"
            db.session.add(new_recomputation_job)
            db.session.commit()
    return redirect(url_for("admin_app.continuous_queries_recomputations"))


@admin_app_blueprint.route("/admin/continuous_queries_recomputations")
@admin_login_required
def continuous_queries_recomputations():
    from database import ContinuousQueryRecomputeJob
    all_recomputations = ContinuousQueryRecomputeJob.query.filter(ContinuousQueryRecomputeJob.state != "finished").all()
    # Compute progress of each recomputation
    for recomputation in all_recomputations:
        if recomputation.last_run_start is None:
            progress = 0
        else:
            time_interval_start_ts = float(time.mktime(recomputation.time_interval_start.timetuple()))
            time_interval_end_ts = float(time.mktime(recomputation.time_interval_end.timetuple()))
            last_run_start_ts = float(time.mktime(recomputation.last_run_start.timetuple()))
            progress = (time_interval_end_ts - last_run_start_ts) / (time_interval_end_ts - time_interval_start_ts)
        recomputation.progress = progress
    all_recomputations = sorted(all_recomputations, key=lambda x: 1 if x.priority == "high" else 2)
    return render_template("continuous_queries_reruns.html.jinja2", all_recomputations=all_recomputations)


@admin_app_blueprint.route("/admin/manage_users.html")
@admin_login_required
def manage_users():
    from database import db
    from database import User as DbUser
    db.session.expire_all()
    users = DbUser.query.all()
    return render_template("settings.html.jinja2", users=users)


@admin_app_blueprint.route("/admin/commands.html")
@admin_login_required
def commands():
    from core.commands.commands import get_commands_arrays, read_modbus_property
    commands = get_commands_arrays()

    for command_name, property_description in commands.items():
        for property_name, property_description in property_description.get("properties", {}).items():
            property_value = read_modbus_property(property_description.get("how"))
            property_description["last_value"] = property_value

    return render_template("commands.html.jinja2", commands=commands)


@admin_app_blueprint.route("/admin/do_action.html&command_name=<command_name>,action_name=<action_name>")
@admin_login_required
def do_action(command_name, action_name):
    from core.commands.commands import get_commands_arrays, modbus_action
    commands = get_commands_arrays()
    print("ici")

    action = commands.get(command_name).get("actions").get(action_name)
    how = action.get("how")

    result = modbus_action(how)

    return redirect(url_for("admin_app.commands"))
