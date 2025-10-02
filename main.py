import os
import logging
from flask import Flask
import werkzeug
import redis
from dotenv import load_dotenv

from utilities.device import Device, Profile
from routes.api import api
from routes.ui import ui
from routes.proxy import proxy
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

load_dotenv()
app = Flask(__name__, static_folder="static")
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(proxy, url_prefix='/proxy')
app.register_blueprint(ui)

app.redis = redis.Redis.from_url(os.getenv('REDIS'))
profile = Profile(
    portal=os.getenv('PORTAL'),
    mac=os.getenv('MAC_ADDRESS'),
    language=os.getenv('STB_LANG'),
    timezone=os.getenv('TZ'),
    device_id=os.getenv('DEVICE_ID'),
    device_id2=os.getenv('DEVICE_ID2'),
    signature=os.getenv('SIGNATURE')
)
app.stb = Device(app.redis, profile)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5123)
