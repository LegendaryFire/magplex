from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, Response, g, jsonify, redirect, request

from magplex.decorators import AuthMethod, authorize_route
from magplex.users import database
from magplex.utilities.error import ErrorResponse
from magplex.utilities.localization import Locale

user = Blueprint("user", __name__)


@user.get('/')
@authorize_route(auth_method=AuthMethod.SESSION)
def get_user():
    user_account = database.get_user(g.db_conn, g.user_session.user_uid)
    return jsonify(user_account)


@user.post('/username')
@authorize_route(auth_method=AuthMethod.SESSION)
def save_username():
    data = request.get_json()
    current_username = data.get('current_username')
    new_username = data.get('new_username')
    password = data.get('password')
    if not current_username or not new_username or not password:
        return ErrorResponse(Locale.GENERAL_MISSING_REQUIRED_FIELDS, HTTPStatus.BAD_REQUEST)
    if any(char.isspace() for char in new_username):
        return ErrorResponse(Locale.UI_USERNAME_CONTAINS_SPACES, HTTPStatus.BAD_REQUEST)

    session_user = database.get_user(g.db_conn, g.user_session.user_uid)
    validated_user = database.validate_user(g.db_conn, session_user.username, password)
    if not validated_user:
        return ErrorResponse(Locale.GENERAL_INVALID_CREDENTIALS, HTTPStatus.FORBIDDEN)

    if new_username == validated_user.username:
        return ErrorResponse(Locale.UI_USERNAME_DIDNT_CHANGE, HTTPStatus.FORBIDDEN)

    database.update_username(g.db_conn, session_user.user_uid, new_username)
    return Response(status=HTTPStatus.OK)


@user.post('/password')
@authorize_route(auth_method=AuthMethod.SESSION)
def save_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    new_password_repeated = data.get('new_password_repeated')

    session_user = database.get_user(g.db_conn, g.user_session.user_uid)
    if not current_password or not new_password or not new_password_repeated:
        return ErrorResponse(Locale.GENERAL_MISSING_REQUIRED_FIELDS, HTTPStatus.BAD_REQUEST)

    validated_user = database.validate_user(g.db_conn, session_user.username, current_password)
    if not validated_user:
        return ErrorResponse(Locale.GENERAL_INVALID_CREDENTIALS, HTTPStatus.FORBIDDEN)

    if len(new_password) < 8:
        return ErrorResponse(Locale.UI_PASSWORD_REQUIREMENT_NOT_MET, HTTPStatus.FORBIDDEN)

    if new_password != new_password_repeated:
        return ErrorResponse(Locale.UI_PASSWORD_DOESNT_MATCH, HTTPStatus.BAD_REQUEST)

    database.update_password(g.db_conn, session_user.user_uid, new_password)
    return Response(status=HTTPStatus.OK)


@user.post('/login')
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return ErrorResponse(Locale.GENERAL_MISSING_REQUIRED_FIELDS, HTTPStatus.BAD_REQUEST)
    user_account = database.validate_user(g.db_conn, username, password)
    if user_account is None:
        return ErrorResponse(Locale.GENERAL_INVALID_CREDENTIALS, HTTPStatus.UNAUTHORIZED)

    expiration_timestamp = datetime.now() + timedelta(days=90)
    user_session = database.insert_user_session(g.db_conn, user_account.user_uid,
                                                      request.remote_addr, expiration_timestamp)

    response = jsonify(user_account)
    response.set_cookie(key='session_uid', value=str(user_session.session_uid), samesite='Lax',
                        httponly=True, secure=False, max_age=90*24*60*60)
    return response


@user.get('/logout')
@authorize_route(auth_method=AuthMethod.SESSION)
def logout():
    user_session = getattr(g, 'user_session', None)
    if user_session is not None:
        database.expire_user_session(g.db_conn, g.user_session.session_uid)
    return redirect('/')


@user.get('/device')
@authorize_route(auth_method=AuthMethod.SESSION)
def get_user_device():
    return jsonify(database.get_device_profile_by_user(g.db_conn, g.user_session.user_uid))


@user.post('/device')
@authorize_route(auth_method=AuthMethod.SESSION)
def save_user_device():
    data = request.get_json()
    mac_address = data.get('mac_address')
    device_id1 = data.get('device_id1')
    device_id2 = data.get('device_id2')
    signature = data.get('signature')
    portal = data.get('portal')
    tz = data.get('timezone')
    database.insert_user_device(g.db_conn, g.user_session.user_uid, mac_address, device_id1, device_id2, signature,
                                       portal, tz)
    return Response(status=HTTPStatus.NO_CONTENT)


@user.get('/api')
@authorize_route(auth_method=AuthMethod.SESSION)
def get_api_key():
    api_key = database.get_api_key(g.db_conn, g.user_session.user_uid)
    return jsonify(api_key)


@user.post('/api')
@authorize_route(auth_method=AuthMethod.SESSION)
def update_api_key():
    database.insert_api_key(g.db_conn, g.user_session.user_uid)
    return Response(status=HTTPStatus.NO_CONTENT)


@user.delete('/api')
@authorize_route(auth_method=AuthMethod.SESSION)
def delete_api_key():
    database.delete_api_key(g.db_conn, g.user_session.user_uid)
    return Response(status=HTTPStatus.NO_CONTENT)

