import json
import logging
import shutil
import subprocess
import threading
from http import HTTPStatus

from flask import Blueprint, Response, current_app, jsonify, request

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
            "GuideName": json.dumps(channel.get('channel_name'), ensure_ascii=True),
            "GuideNumber": channel.get('channel_id'),
            "URL": f"{domain}/stb/channels/{channel.get('stream_id')}"
        })

    return jsonify(channel_lineup)


@stb.route('/channels/<int:stream_id>')
def get_channel_playlist(stream_id):
    channel_url = current_app.stb.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to retrieve channel.", status=HTTPStatus.NOT_FOUND)

    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        return Response("Unable to find ffmpeg installation.", status=HTTPStatus.INTERNAL_SERVER_ERROR)

    ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-allowed_extensions", "ALL",
        "-i", channel_url,
        "-c", "copy",
        "-f", "mpegts",
        "pipe:1"
    ]
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def log_errors():
        for line in iter(process.stderr.readline, b""):
            logging.error(line.decode(errors="ignore").strip())
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
