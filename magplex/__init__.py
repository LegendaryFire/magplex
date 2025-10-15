from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from magplex.routes.api import api
from magplex.routes.proxy import proxy
from magplex.routes.stb import stb
from magplex.routes.ui import ui


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(stb, url_prefix='/stb')
    app.register_blueprint(proxy, url_prefix='/proxy')
    app.register_blueprint(ui)
