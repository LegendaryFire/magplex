from functools import wraps

from flask import g, redirect


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not getattr(g, "user_session", None):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated