import json
from http import HTTPStatus

from flask import Flask, g, Request
from werkzeug.middleware.proxy_fix import ProxyFix

import magplex.database as database
from magplex import users
from magplex.database.database import PostgresConnection, RedisPool
from magplex.routes.device import device
from magplex.routes.stb import stb
from magplex.routes.ui import ui
from magplex.routes.user import user
from magplex.utilities.error import ErrorResponse, InvalidJsonError
from magplex.utilities.localization import Locale
from magplex.utilities.serializers import StrictJSONProvider


class CustomRequest(Request):
    def on_json_loading_failed(self, e):
        raise InvalidJsonError


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.register_blueprint(user, url_prefix="/api/user")
    app.register_blueprint(device, url_prefix='/api/devices')
    app.register_blueprint(stb, url_prefix='/api/devices')
    app.register_blueprint(ui)


    @app.before_request
    def before_request():
        g.db_conn = PostgresConnection()
        g.cache_conn = RedisPool.get_connection()


    @app.teardown_request
    def teardown_request(exception=None):
        try:
            if exception:
                g.db_conn.rollback()
            else:
                g.db_conn.commit()
        finally:
            g.db_conn.close()

    @app.errorhandler(InvalidJsonError)
    def handle_bad_request(e):
        return ErrorResponse(Locale.GENERAL_EXPECTED_JSON, status=HTTPStatus.BAD_REQUEST)

    app.request_class = CustomRequest
    return app
