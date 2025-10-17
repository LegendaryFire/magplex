from flask import Flask, g, request
from werkzeug.middleware.proxy_fix import ProxyFix

import magplex.database as database
from magplex.routes.channels import channels
from magplex.routes.proxy import proxy
from magplex.routes.stb import stb
from magplex.routes.ui import ui
from magplex.utilities.database import RedisPool, LazyPostgresConnection


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.register_blueprint(channels, url_prefix='/api/channels')
    app.register_blueprint(stb, url_prefix='/stb')
    app.register_blueprint(proxy, url_prefix='/proxy')
    app.register_blueprint(ui)

    @app.before_request
    def before_request():
        g.db_conn = LazyPostgresConnection()
        g.cache_conn = RedisPool.get_connection()

    @app.teardown_request
    def teardown_request(exception=None):
        db_conn = getattr(g, 'db_conn', None)
        if db_conn:
            try:
                if exception:
                    db_conn.rollback()
                else:
                    db_conn.commit()
            finally:
                db_conn.put_connection()

    return app
