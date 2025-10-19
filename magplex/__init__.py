from flask import Flask, g, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

import magplex.database as database
from magplex.routes.device import device
from magplex.routes.proxy import proxy
from magplex.routes.stb import stb
from magplex.routes.ui import ui
from magplex.routes.user import user
from magplex.utilities.database import RedisPool, LazyPostgresConnection
from magplex.utilities.error import ErrorResponse


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.register_blueprint(user, url_prefix="/api/user")
    app.register_blueprint(device, url_prefix='/api/device')
    app.register_blueprint(proxy, url_prefix='/api/proxy')
    app.register_blueprint(stb, url_prefix='/stb')
    app.register_blueprint(ui)

    @app.before_request
    def before_request():
        g.db_conn = LazyPostgresConnection()
        g.cache_conn = RedisPool.get_connection()
        session_uid = request.cookies.get('session_uid')
        if session_uid:
            with LazyPostgresConnection() as conn:
                g.user_session = database.users.get_user_session(conn, session_uid)

    @app.teardown_request
    def teardown_request(exception=None):
        try:
            if exception:
                g.db_conn.rollback()
            else:
                g.db_conn.commit()
        finally:
            g.db_conn.close()

    return app
