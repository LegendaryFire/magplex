from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, request, Response, g, jsonify, redirect

from magplex import database
from magplex.decorators import login_required

user = Blueprint("user", __name__)

@user.post('/login')
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return Response('Missing mandatory parameters.', HTTPStatus.BAD_REQUEST)
    user = database.users.validate_user(g.db_conn, username, password)
    if user is None:
        return Response('Invalid user credentials.', HTTPStatus.UNAUTHORIZED)

    expiration_timestamp = datetime.now() + timedelta(days=90)
    user_session = database.users.insert_user_session(g.db_conn, user.user_uid, request.remote_addr, expiration_timestamp)

    response = jsonify(user)
    response.set_cookie(key='session_uid', value=str(user_session.session_uid), samesite='Lax',
                        httponly=True, secure=False, max_age=90*24*60*60)
    return response


@user.route('/logout')
def logout():
    user_session = getattr(g, 'user_session', None)
    if user_session is not None:
        database.users.expire_user_session(g.db_conn, g.user_session.session_uid)
    return redirect('/api/users/login')


@user.route('/devices')
@login_required
def user_devices():
    return jsonify(database.device.get_user_devices(g.db_conn, g.user_session.user_uid))