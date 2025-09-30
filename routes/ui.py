from http import HTTPStatus

from flask import Blueprint, render_template, send_file, Response
from version import __version__


ui = Blueprint("ui", __name__)

@ui.route('/')
def index():
    return render_template('index.html')

@ui.route('/logs')
def logs():
    try:
        return send_file(f'logs/v{__version__}.log', as_attachment=False)
    except FileNotFoundError:
        return Response("Could not find log file.", HTTPStatus.NOT_FOUND)
