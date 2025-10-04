import logging
import os
import sys

import redis
import werkzeug
from flask import Flask

from routes.api import api
from routes.proxy import proxy
from routes.ui import ui
from utilities.device import Device, Profile
from utilities.environment import Variables
from version import __version__

# Set up logs, ensure logs folder exists.
if not os.path.exists('logs'):
    os.makedirs('logs')

# Disable color logging style.
werkzeug.serving._log_add_style = False

# Set up global logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[
        logging.FileHandler(f'logs/v{__version__}.log'),
        logging.StreamHandler()  # Optional: also log to console
    ]
)

logging.info(f"MagPlex Version {__version__} by Tristan Balon")

if not Variables.valid():
    logging.error("Missing environment variables.")
    sys.exit()

app = Flask(__name__, static_folder="static")
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(proxy, url_prefix='/proxy')
app.register_blueprint(ui)

app.redis = redis.Redis(host=Variables.REDIS_HOST, port=Variables.REDIS_PORT, db=0)
try:
    app.redis.ping()
except redis.exceptions.RedisError:
    logging.error("Unable to connect to Redis server. Please try again...")
    sys.exit()

profile = Profile(
    portal=Variables.STB_PORTAL,
    mac=Variables.STB_MAC,
    language=Variables.STB_LANGUAGE,
    timezone=Variables.STB_TIMEZONE,
    device_id=Variables.STB_DEVICE_ID,
    device_id2=Variables.STB_DEVICE_ID2,
    signature=Variables.STB_SIGNATURE
)
app.stb = Device(app.redis, profile)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5123)
