import logging
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from flask import (Blueprint, Response, g, jsonify, redirect, render_template,
                   request, send_file)

import magplex.database as database
import version
from magplex.decorators import login_required
from magplex.utilities.device import DeviceManager
from magplex.utilities.environment import Variables
from magplex.utilities.scheduler import TaskManager

ui = Blueprint("ui", __name__)


@ui.get('/login')
def login_page():
    return render_template('login.html')


@ui.post('/login')
def login_attempt():
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


@ui.route('/logout')
def logout():
    user_session = getattr(g, 'user_session', None)
    if user_session is not None:
        database.users.expire_user_session(g.db_conn, g.user_session.session_uid)
    return redirect('/login')


@ui.route('/')
@login_required
def index():
    return render_template('index.html')


@ui.route('/logs')
@login_required
def logs():
    try:
        return send_file(Variables.BASE_LOG, as_attachment=False)
    except FileNotFoundError:
        return Response("Could not find log file.", HTTPStatus.NOT_FOUND)


@ui.route('/about')
@login_required
def get_about():
    return jsonify({
        'version': version.version,
        'build_date': getattr(version, "build_date", "Unknown")
    })


@ui.get('/device')
@login_required
def get_device():
    device = database.device.get_user_device(g.db_conn)
    return jsonify(device)

@ui.post('/device')
@login_required
def save_device():
    mac_address = request.json.get('mac_address')
    device_id1 = request.json.get('device_id1')
    device_id2 = request.json.get('device_id2')
    signature = request.json.get('signature')
    portal = request.json.get('portal')
    language = request.json.get('language')
    tz = request.json.get('timezone')
    database.device.save_user_device(g.db_conn, g.user_session.user_uid, mac_address, device_id1, device_id2, signature,
                                     portal, language, tz)
    DeviceManager.reset_device()
    return Response(status=HTTPStatus.NO_CONTENT)


@ui.get('/user')
@login_required
def get_user():
    user = database.users.get_user(g.db_conn, g.user_session.user_uid)
    return jsonify(user)

@ui.post('/refresh-epg')
@login_required
def refresh_epg():
    scheduler = TaskManager.get_scheduler()
    device = DeviceManager.get_device()
    job = scheduler.get_job(device.id)
    if not job:
        logging.warning(f"Could not find job located in job store.")
        return Response(status=HTTPStatus.NOT_FOUND)

    job.modify(next_run_time=datetime.now(timezone.utc))
    logging.info(f"Manually triggered EPG refresh for device {device.id}.")
    return Response(status=HTTPStatus.ACCEPTED)


@ui.post('/user')
@login_required
def save_user():
    # Start by validating the current password against the user.
    session_user = database.users.get_user(g.db_conn, g.user_session.user_uid)
    current_password = request.json.get('current_password')
    validated_user = database.users.validate_user(g.db_conn, session_user.username, current_password)
    if not validated_user:
        return Response("Invalid password, please try again.", HTTPStatus.BAD_REQUEST)

    username = request.json.get('username')
    if ' ' in username:
        return Response("Username can't contain spaces.", HTTPStatus.BAD_REQUEST)
    if not username or len(username) < 8:
        return Response("Username must be at least 8 characters long.", HTTPStatus.BAD_REQUEST)
    if username != session_user.username:
        database.users.update_username(g.db_conn, session_user.user_uid, username)

    new_password = request.json.get('new_password')
    new_password_confirmed = request.json.get('new_password_confirmed')
    if len(new_password) < 8:
        return Response("Password must be at least 8 characters long.", HTTPStatus.BAD_REQUEST)
    if new_password == new_password_confirmed:
        database.users.update_password(g.db_conn, session_user.user_uid, new_password)
    else:
        return Response("Passwords entered did not match. Please try again.", status=HTTPStatus.BAD_REQUEST)

    return Response(status=HTTPStatus.NO_CONTENT)
