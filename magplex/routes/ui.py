from http import HTTPStatus

from flask import Blueprint, Response, render_template, send_file

from magplex.utilities.environment import Variables

ui = Blueprint("ui", __name__)

@ui.route('/')
def index():
    return render_template('index.html')

@ui.route('/logs')
def logs():
    try:
        return send_file(Variables.BASE_LOG, as_attachment=False)
    except FileNotFoundError:
        return Response("Could not find log file.", HTTPStatus.NOT_FOUND)
