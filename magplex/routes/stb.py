import logging
from http import HTTPStatus

import ffmpeg
import requests
from flask import Blueprint, Response, jsonify, request

from magplex.utilities import media, parser
from magplex.utilities.device import DeviceManager
from magplex.utilities.variables import Environment

stb = Blueprint("stb", __name__)


@stb.route('/')
def root():
    device = DeviceManager.get_device()
    if device is None:
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
            <serialNumber>{device.id}</serialNumber>
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
    device = DeviceManager.get_device()
    if device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    channel_list = device.get_channel_list()
    channel_lineup = []
    for channel in channel_list:
        channel_lineup.append({
            "GuideName": channel.get('channel_name'),
            "GuideNumber": channel.get('channel_id'),
            "URL": f"{domain}/channels/{channel.get('stream_id')}"
        })

    return jsonify(channel_lineup)


@stb.route('/channels/<int:stream_id>')
def get_channel_playlist(stream_id):
    device = DeviceManager.get_device()
    if device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    channel_url = device.get_channel_playlist(stream_id)
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
    channel_url = f'{domain}/proxy/channels/{stream_id}'

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

@stb.route('/channels/guide.xml')
def get_channel_guide():
    device = DeviceManager.get_device()
    if device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    data = device.get_channel_guide()
    guide = parser.build_channel_guide(data.get('channels'), data.get('channel_guides'))
    return Response(guide, mimetype='text/xml')