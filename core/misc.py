intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),  # 60 * 60 * 24
    ('hours', 3600),  # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)


def prettify_duration(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    diff = dt

    nb_seconds = diff % 60
    nb_minutes = (diff - nb_seconds) / 60
    nb_hours = (diff - nb_seconds - nb_minutes * 60) / 3600

    periods = (
        (nb_hours, "hour", "hours"),
        (nb_minutes, "minute", "minutes"),
        (nb_seconds, "second", "seconds"),
    )

    result = []

    for period, singular, plural in periods:
        # if period:
        result += ["%d %s" % (period, singular if period == 1 else plural)]

    return ", ".join(result)


def _display_time(seconds, granularity=2):
    if seconds < 1.0:
        return "now"
    if seconds > 3600:
        return "more than one hour"

    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def ensure_admin_user_exists(db):
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
