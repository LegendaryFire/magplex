from functools import wraps

from flask import g, redirect, request

import magplex.database as database


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_uid = request.cookies.get('session_uid')
        if session_uid:
            conn = g.db_conn.get_connection()
            g.user_session = database.users.get_user_session(conn, session_uid)
        else:
            g.user_session = None

        if not getattr(g, "user_session", None):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated