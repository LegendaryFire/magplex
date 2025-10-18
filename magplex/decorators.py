from functools import wraps

from flask import g, redirect, request

import magplex.database as database
from magplex.utilities.database import LazyPostgresConnection


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_uid = request.cookies.get('session_uid')
        if session_uid:
            with LazyPostgresConnection() as conn:
                g.user_session = database.users.get_user_session(conn, session_uid)
        else:
            g.user_session = None

        if not getattr(g, "user_session", None):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated