import json
import logging
import shutil
import ffmpeg
import threading
from http import HTTPStatus

import requests
from flask import Blueprint, Response, current_app, jsonify, request

from magplex.utilities.environment import Variables

stb = Blueprint("stb", __name__)


@stb.route('/')
def root():
    domain = request.host_url[:-1]
    return Response(f"""
    <root>
        <URLBase>{domain}</URLBase>
        <specVersion>
        <major>1</major>
        <minor>0</minor>
        </specVersion>
        <device>
            <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
            <friendlyName>Magplex</friendlyName>
            <manufacturer>Silicondust</manufacturer>
            <modelName>HDTC-2US</modelName>
            <modelNumber>HDTC-2US</modelNumber>
            <serialNumber>{current_app.stb.id}</serialNumber>
            <UDN>uuid:2025-10-FBE0-RLST64</UDN>
        </device>
    </root>
    """, mimetype='text/xml')


@stb.route('/discover.json')
def discover():
    domain = request.host_url[:-1]
    return jsonify({
        "BaseURL": domain,
        "DeviceAuth": "Magplex",
        "DeviceID": "2025-10-FBE0-RLST64",
        "FirmwareName": "bin_1.2",
        "FirmwareVersion": "1.2",
        "FriendlyName": "Magplex",
        "LineupURL": f"{domain}/stb/lineup.json",
        "Manufacturer": "LegendaryFire",
        "ModelNumber": "1.2",
        "TunerCount": 1
    })

@stb.route('/lineup_status.json')
def lineup_status():
    return jsonify({
        "ScanInProgress": 0,
        "ScanPossible": 1,
        "Source": "Cable",
        "Lineup": "Complete"
    })

@stb.route('/lineup.json')
def lineup():
    domain = request.host_url[:-1]
    channel_list = current_app.stb.get_channel_list()
    channel_lineup = []
    for channel in channel_list:
        channel_lineup.append({
            "GuideName": channel.get('channel_name'),
            "GuideNumber": channel.get('channel_id'),
            "URL": f"{domain}/stb/channels/{channel.get('stream_id')}"
        })

    return jsonify(channel_lineup)


@stb.route('/channels/<int:stream_id>')
def get_channel_playlist(stream_id):
    channel_url = current_app.stb.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to retrieve channel.", status=HTTPStatus.NOT_FOUND)

    if Variables.BASE_FFMPEG is None:
        logging.error("Unable to find ffmpeg installation.")
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # Attempt to get X-Sid header if it exists.
    response = requests.get(channel_url, stream=True, allow_redirects=True)

    # Pass session header and others if they exist.
    forward_headers = {}
    for key in ['X-Sid', 'User-Agent', 'Referer', 'Origin']:
        if key in response.headers:
            forward_headers[key] = response.headers[key]
    forward_headers = ''.join(f"{k}: {v}\r\n" for k, v in forward_headers.items())

    try:
        process = (
            ffmpeg
            .input(
                channel_url,
                re=None,
                allowed_extensions='ALL',
                http_persistent=1,
                **{'headers': forward_headers}
            )
            .output(
                'pipe:1',
                format='mpegts',
                codec='copy',
                **{'headers': forward_headers}
            )
            .run_async(cmd=Variables.BASE_FFMPEG, pipe_stdout=True, pipe_stderr=False)
        )
    except ffmpeg.Error as e:
        logging.error(e.stderr.decode())
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_errors():
        for line in iter(process.stderr.readline, b''):
            logging.error(line.decode(errors='ignore').strip())
    threading.Thread(target=log_errors, daemon=True).start()

    def generate():
        try:
            while True:
                data = process.stdout.read(64 * 1024)  # 64KB
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(
        generate(),
        headers={
            "Content-Type": "video/mp2t",
            "Access-Control-Allow-Origin": "*"
        }
    )
