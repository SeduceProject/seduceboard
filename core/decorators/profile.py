from pyinstrument import Profiler
from flask_login.utils import wraps, current_app, current_user, request
from flask_login.config import EXEMPT_METHODS


def profile(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):

        profiler = Profiler()
        profiler.start()

        result = func(*args, **kwargs)

        profiler.stop()

        print(profiler.output_text(unicode=True, color=True))

        return result

    return decorated_view
