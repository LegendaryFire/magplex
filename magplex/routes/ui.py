import logging
from http import HTTPStatus

from flask import Blueprint, Response, jsonify, render_template, send_file, request, make_response, g

import version
from magplex.utilities.error import ErrorResponse
from magplex.decorators import AuthMethod, authorize_route
from magplex.utilities.localization import Locale
from magplex.utilities.variables import Environment
from magplex.device import database

ui = Blueprint("ui", __name__)


@ui.get('/login')
def login_page():
    return render_template('login.html')


@ui.route('/')
@authorize_route(auth_method=AuthMethod.SESSION, force_redirect=True)
def index():
    return render_template('index.html')


@ui.route('/logs')
@authorize_route(auth_method=AuthMethod.SESSION)
def logs():
    try:
        return send_file(Environment.BASE_LOG, as_attachment=False)
    except FileNotFoundError:
        return Response(Locale.LOG_FILE_NOT_FOUND, HTTPStatus.NOT_FOUND)


@ui.route('/about')
@authorize_route(auth_method=AuthMethod.SESSION)
def get_about():
    return jsonify({
        'version': version.version,
        'build_date': getattr(version, "build_date", "Unknown")
    })


@ui.get("/stalker")
def portal_root():
    return make_response(render_template('portal.html'), 200, {
        "Content-Type": "text/html; charset=utf-8",
        "Connection": "Keep-Alive"
    })


@ui.post("/stalker")
def get_ids():
    payload = request.get_json()
    mac_address = payload.get('mac_address')
    device_id1 = payload.get('device_id1')
    device_id2 = payload.get('device_id2')

    if device_id1 is None or device_id2 is None or mac_address is None:
        return ErrorResponse("Unable to get device information.", HTTPStatus.BAD_REQUEST)

    database.update_device_id(g.db_conn, mac_address, device_id1, device_id2)
    logging.info(f"Device ID updated for MAC address: {mac_address}.")
    return Response(status=200)