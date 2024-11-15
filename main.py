import os
import threading
import time
import requests
import logging
from flask import Flask, request, Response, redirect, send_file
import helper
import stb
from cache import ttl_cache
import werkzeug
from version import __version__

# Begin set up of logs, ensure logs folder exists.
if not os.path.exists('logs'):
    os.makedirs('logs')

# Disable color logging style.
werkzeug.serving._log_add_style = False

# Set up global logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()  # Optional: also log to console
    ]
)

logging.info(f"MagPlex Version {__version__} by Tristan Balon")
app = Flask(__name__)

profile = stb.STBProfile(
    portal=os.getenv('PORTAL'),
    mac_address=os.getenv('MAC_ADDRESS'),
    stb_lang=os.getenv('STB_LANG'),
    timezone=os.getenv('TZ'),
    device_id=os.getenv('DEVICE_ID'),
    device_id2=os.getenv('DEVICE_ID2'),
    signature=os.getenv('SIGNATURE')
)
instance = stb.STB(profile)


@app.route('/channel/<channel_id>')
def channel(channel_id):
    channel_url = instance.get_channel_url(channel_id)
    return redirect(channel_url, code=302)


@app.route('/channel_list.m3u8')
def channel_list():
    domain = request.host_url[:-1]
    channels = instance.get_channel_list()
    playlist = helper.build_playlist(channels, domain)
    return Response(playlist, mimetype='audio/x-mpegurl')


@app.route('/channel_guide.xml')
def channel_guide():
    guide = get_channel_guide()
    return Response(guide, mimetype='text/xml')


@app.route('/logs')
def logs():
    try:
        return send_file('logs/app.log', as_attachment=False)
    except FileNotFoundError:
        return "Could not find log file.", 404


@ttl_cache(ttl_seconds=int(os.getenv('CACHE_EXPIRATION')))
def get_channel_guide():
    channels = instance.get_channel_list()
    guides = instance.get_channel_guide()
    guide = helper.build_channel_guide(channels, guides)
    return guide


def refresh_plex_epg():
    """Refreshes the Plex guide at a given interval."""
    while True:
        plex_url = f'http://{plex_server_ip}/livetv/dvrs/{plex_dvr_id}/reloadGuide?X-Plex-Token={plex_token}'
        response = requests.post(plex_url)
        if response.status_code != 200:
            logging.warning("Failed to update Plex EPG data.")
        else:
            logging.info("Refreshed Plex EPG data.")
        time.sleep(int(plex_refresh))


# Automatically update the Plex EPG at the set interval if environment variables are set.
plex_refresh, plex_dvr_id, plex_server_ip, plex_token = os.getenv('PLEX_REFRESH'), os.getenv('PLEX_DVR'), os.getenv('PLEX_SERVER'), os.getenv('PLEX_TOKEN')
if all([plex_server_ip, plex_token, str(plex_dvr_id).isdigit(), str(plex_refresh).isdigit()]):
    thread = threading.Thread(target=refresh_plex_epg)
    thread.start()

# Start MAG box interpreter server.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5123, debug=False)
