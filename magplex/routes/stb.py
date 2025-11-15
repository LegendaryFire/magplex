import logging
import threading
from http import HTTPStatus

import requests
from flask import Blueprint, Response, g, jsonify, request, stream_with_context

from magplex.decorators import AuthMethod, authorize_route
from magplex.device import database, media
from magplex.device.manager import DeviceManager
from magplex.stb import parser
from magplex.utilities.error import ErrorResponse
from magplex.utilities.localization import Locale
from magplex.utilities.variables import Environment

stb = Blueprint("stb", __name__)


@stb.get('/<uuid:device_uid>/stb/')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_root(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return Response(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    return Response(parser.build_device_info(user_device.device_uid, domain), mimetype='text/xml')


@stb.get('/<uuid:device_uid>/stb/discover.json')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_discover(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    return jsonify(parser.build_discover(domain))


@stb.get('/<uuid:device_uid>/stb/lineup_status.json')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_lineup_status(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    return jsonify(parser.build_status())


@stb.get('/<uuid:device_uid>/stb/lineup.json')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_lineup(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return Response(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    channel_list = database.get_channels(g.db_conn, user_device.device_uid, channel_enabled=True)
    return jsonify([parser.build_lineup_channel(channel, domain) for channel in channel_list if channel])


@stb.get('/<uuid:device_uid>/stb/<int:channel_id>/stream.ts')
def get_stb_channel_playlist(device_uid, channel_id):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    channel = database.get_channel(g.db_conn, device_uid, channel_id)
    if channel is None:
        return ErrorResponse(Locale.DEVICE_CHANNEL_PLAYLIST_UNAVAILABLE, status=HTTPStatus.NOT_FOUND)

    if Environment.BASE_FFMPEG is None:
        logging.error("Unable to find ffmpeg installation.")
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    encoder = media.get_encoder()
    def stream_generator():
        process = None
        try:
            while True:
                channel_url = user_device.get_channel_playlist(channel.stream_id)
                logging.error(channel_url)
                if not channel_url:
                    break
                r = requests.get(channel_url, allow_redirects=True)
                headers = ''.join(f"{k}: {v}\r\n" for k, v in r.headers.items() if k in ['X-Sid', 'User-Agent', 'Referer', 'Origin'])
                process = media.create_stream_response(channel_url, encoder, headers)
                for chunk in iter(lambda: process.stdout.read(64 * 1024), b''):
                    yield chunk
        finally:
            if process:
                try:
                    process.terminate()
                except Exception:
                    pass
                threading.Thread(target=lambda p: (p.wait() or p.kill()), args=(process,), daemon=True).start()
                try:
                    process.stdout.close()
                except Exception:
                    pass

    return Response(
        stream_with_context(stream_generator()),
        direct_passthrough=True,
        headers={
            "Content-Type": "video/mp2t",
            "Access-Control-Allow-Origin": "*"
        }
    )


@stb.get('/<uuid:device_uid>/stb/guide.xml')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_channel_guide(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return Response(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    channels = database.get_channels(g.db_conn, user_device.device_uid, channel_enabled=True)
    guides = database.get_current_channel_guides(g.db_conn, user_device.device_uid)
    guide = parser.build_channel_guide(channels, guides)
    return Response(guide, mimetype='text/xml')

