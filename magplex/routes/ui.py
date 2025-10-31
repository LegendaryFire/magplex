from http import HTTPStatus

from flask import Blueprint, Response, jsonify, render_template, send_file

import version
from magplex.decorators import login_required
from magplex.utilities.variables import Environment

ui = Blueprint("ui", __name__)


@ui.get('/login')
def login_page():
    return render_template('login.html')


@ui.route('/')
@login_required
def index():
    return render_template('index.html')


@ui.route('/logs')
@login_required
def logs():
    try:
        return send_file(Environment.BASE_LOG, as_attachment=False)
    except FileNotFoundError:
        return Response("Could not find log file.", HTTPStatus.NOT_FOUND)


@ui.route('/about')
@login_required
def get_about():
    return jsonify({
        'version': version.version,
        'build_date': getattr(version, "build_date", "Unknown")
    })
