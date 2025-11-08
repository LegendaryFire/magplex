from http import HTTPStatus

from flask import Blueprint, Response, jsonify, render_template, send_file

import version
from magplex.decorators import AuthMethod, authorize_route
from magplex.utilities.localization import Locale
from magplex.utilities.variables import Environment

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
