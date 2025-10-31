import logging
from http import HTTPStatus

import ffmpeg
import requests
from flask import Blueprint, Response, g, jsonify, request

from magplex.device import database
from magplex.device.device import DeviceManager
from magplex.device.localization import ErrorMessage
from magplex.stb import parser
from magplex.utilities import media
from magplex.utilities.variables import Environment

stb = Blueprint("stb", __name__)


@stb.route('/')
def root():
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
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
            <serialNumber>{user_device.device_uid}</serialNumber>
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
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    channel_list = database.get_enabled_channels(g.db_conn, user_device.device_uid)
    for i, channel in enumerate(channel_list):
        channel_list[i] = {
            "GuideName": channel.channel_name,
            "GuideNumber": channel.channel_id,
            "URL": f"{domain}/stb/playlist.m3u8?stream_id={channel.stream_id}"
        }

    return jsonify(channel_list)


@stb.route('/playlist.m3u8')
def get_channel_playlist():
    stream_id = request.args.get('stream_id')
    if stream_id is None:
        return Response("Missing required parameter 'stream_id'.", status=HTTPStatus.BAD_REQUEST)

    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.BAD_REQUEST)

    channel_url = user_device.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to retrieve channel.", status=HTTPStatus.NOT_FOUND)

    # Attempt to get X-Sid header if it exists.
    response = requests.get(channel_url, stream=True, allow_redirects=True)

    # Pass session header and others if they exist.
    headers = {}
    for key in ['X-Sid', 'User-Agent', 'Referer', 'Origin']:
        if key in response.headers:
            headers[key] = response.headers[key]
    headers = ''.join(f"{k}: {v}\r\n" for k, v in headers.items())

    domain = request.host_url[:-1]
    channel_url = f'{domain}/api/proxy/channels/{stream_id}'

    if Environment.BASE_FFMPEG is None:
        logging.error("Unable to find ffmpeg installation.")
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    encoder = media.get_encoder()
    try:
        process = media.create_stream_response(channel_url, encoder, headers)
    except ffmpeg.Error as e:
        logging.error(e.stderr.decode())
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

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


@stb.get('/guide.xml')
def get_channel_guide():
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    channels = database.get_enabled_channels(g.db_conn, user_device.device_uid)
    guides = database.get_all_channel_guides(g.db_conn, user_device.device_uid)
    genres = database.get_genres(g.db_conn, user_device.device_uid)
    guide = parser.build_channel_guide(channels, guides)
    return Response(guide, mimetype='text/xml')

