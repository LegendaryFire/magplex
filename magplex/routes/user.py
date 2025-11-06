from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, Response, g, jsonify, redirect, request

from magplex.decorators import authorize_route, AuthMethod
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
    current_username = request.json.get('current_username')
    new_username = request.json.get('new_username')
    password = request.json.get('password')
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
    current_password = request.json.get('current_password')
    new_password = request.json.get('new_password')
    new_password_repeated = request.json.get('new_password_repeated')

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
    username = request.json.get('username')
    password = request.json.get('password')
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


@user.route('/logout')
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
    mac_address = request.json.get('mac_address')
    device_id1 = request.json.get('device_id1')
    device_id2 = request.json.get('device_id2')
    signature = request.json.get('signature')
    portal = request.json.get('portal')
    language = request.json.get('language')
    tz = request.json.get('timezone')
    database.insert_user_device(g.db_conn, g.user_session.user_uid, mac_address, device_id1, device_id2, signature,
                                       portal, language, tz)
    return Response(status=HTTPStatus.NO_CONTENT)
