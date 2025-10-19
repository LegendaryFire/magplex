from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, request, Response, g, jsonify, redirect

from magplex import database
from magplex.decorators import login_required
from magplex.utilities.device import DeviceManager
from magplex.utilities.error import ErrorResponse

user = Blueprint("user", __name__)


@user.get('/')
@login_required
def get_user():
    user_account = database.users.get_user(g.db_conn, g.user_session.user_uid)
    return jsonify(user_account)


@user.post('/username')
@login_required
def save_username():
    current_username = request.json.get('current_username')
    new_username = request.json.get('new_username')
    password = request.json.get('password')
    if not current_username or not new_username or not password:
        return ErrorResponse("Missing required fields.", HTTPStatus.BAD_REQUEST)
    if any(char.isspace() for char in new_username):
        return ErrorResponse("New username can't contain spaces.", HTTPStatus.BAD_REQUEST)

    session_user = database.users.get_user(g.db_conn, g.user_session.user_uid)
    validated_user = database.users.validate_user(g.db_conn, session_user.username, password)
    if not validated_user:
        return ErrorResponse("Invalid credentials, please try again.", HTTPStatus.FORBIDDEN)

    if new_username == validated_user.username:
        return ErrorResponse("New username is the same as current.", HTTPStatus.FORBIDDEN)

    database.users.update_username(g.db_conn, session_user.user_uid, new_username)
    return Response(status=HTTPStatus.OK)


@user.post('/password')
@login_required
def save_password():
    current_password = request.json.get('current_password')
    new_password = request.json.get('new_password')
    new_password_repeated = request.json.get('new_password_repeated')

    session_user = database.users.get_user(g.db_conn, g.user_session.user_uid)
    if not current_password or not new_password or not new_password_repeated:
        return ErrorResponse("Missing required fields.", HTTPStatus.BAD_REQUEST)

    validated_user = database.users.validate_user(g.db_conn, session_user.username, current_password)
    if not validated_user:
        return ErrorResponse("Invalid credentials, please try again.", HTTPStatus.FORBIDDEN)

    if len(new_password) < 8:
        return ErrorResponse("New password must be at least 8 characters long.", HTTPStatus.FORBIDDEN)

    if new_password != new_password_repeated:
        return ErrorResponse("The new passwords do not match, please try again.", HTTPStatus.BAD_REQUEST)

    database.users.update_password(g.db_conn, session_user.user_uid, new_password)
    return Response(status=HTTPStatus.OK)


@user.post('/login')
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return Response('Missing mandatory parameters.', HTTPStatus.BAD_REQUEST)
    user_account = database.users.validate_user(g.db_conn, username, password)
    if user_account is None:
        return Response('Invalid user credentials.', HTTPStatus.UNAUTHORIZED)

    expiration_timestamp = datetime.now() + timedelta(days=90)
    user_session = database.users.insert_user_session(g.db_conn, user_account.user_uid,
                                                      request.remote_addr, expiration_timestamp)

    response = jsonify(user_account)
    response.set_cookie(key='session_uid', value=str(user_session.session_uid), samesite='Lax',
                        httponly=True, secure=False, max_age=90*24*60*60)
    return response


@user.route('/logout')
def logout():
    user_session = getattr(g, 'user_session', None)
    if user_session is not None:
        database.users.expire_user_session(g.db_conn, g.user_session.session_uid)
    return redirect('/')


@user.get('device')
@login_required
def get_user_device():
    return jsonify(database.device.get_user_device(g.db_conn))


@user.post('/device')
@login_required
def save_user_device():
    mac_address = request.json.get('mac_address')
    device_id1 = request.json.get('device_id1')
    device_id2 = request.json.get('device_id2')
    signature = request.json.get('signature')
    portal = request.json.get('portal')
    language = request.json.get('language')
    tz = request.json.get('timezone')
    database.device.insert_user_device(g.db_conn, g.user_session.user_uid, mac_address, device_id1, device_id2, signature,
                                       portal, language, tz)
    DeviceManager.reset_device()
    return Response(status=HTTPStatus.NO_CONTENT)
