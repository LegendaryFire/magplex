import os
import logging
from flask import Flask
import werkzeug

from utilities import stb
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
app = Flask(__name__, static_folder="static")
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(proxy, url_prefix='/proxy')
app.register_blueprint(ui)

profile = stb.STBProfile(
    portal=os.getenv('PORTAL'),
    mac_address=os.getenv('MAC_ADDRESS'),
    stb_lang=os.getenv('STB_LANG'),
    timezone=os.getenv('TZ'),
    device_id=os.getenv('DEVICE_ID'),
    device_id2=os.getenv('DEVICE_ID2'),
    signature=os.getenv('SIGNATURE')
)

app.stb = stb.STB(profile)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5123, debug=True)
