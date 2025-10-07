import logging
import sys

import redis
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from magplex.routes.api import api
from magplex.routes.proxy import proxy
from magplex.routes.stb import stb
from magplex.routes.ui import ui
from magplex.utilities import logs
from magplex.utilities.device import Device, Profile
from magplex.utilities.environment import Variables
from version import version

logs.initialize()
logging.info(f"MagPlex v{version} by LegendaryFire")

if not Variables.valid():
    logging.error("Missing environment variables.")
    sys.exit()

app = Flask(__name__, static_folder="magplex/static", template_folder="magplex/templates")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(stb, url_prefix='/stb')
app.register_blueprint(proxy, url_prefix='/proxy')
app.register_blueprint(ui)

conn = redis.Redis(host=Variables.REDIS_HOST, port=Variables.REDIS_PORT, db=0)
try:
    conn.ping()
except redis.exceptions.RedisError:
    logging.error("Unable to connect to Redis server. Please try again...")
    sys.exit()

jobstores = {'default': RedisJobStore(host=Variables.REDIS_HOST, port=Variables.REDIS_PORT, db=1)}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

profile = Profile(
    portal=Variables.STB_PORTAL,
    mac=Variables.STB_MAC,
    language=Variables.STB_LANGUAGE,
    timezone=Variables.STB_TIMEZONE,
    device_id=Variables.STB_DEVICE_ID,
    device_id2=Variables.STB_DEVICE_ID2,
    signature=Variables.STB_SIGNATURE
)

app.stb = Device(conn, scheduler, profile)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, use_reloader=True, debug=True)
