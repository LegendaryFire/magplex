import logging
from http import HTTPStatus
from subprocess import TimeoutExpired

import ffmpeg
import requests
from flask import Blueprint, Response, g, jsonify, request, stream_with_context

from magplex.utilities.error import ErrorResponse
from magplex.decorators import authorize_route, AuthMethod
from magplex.device import database, media
from magplex.device.manager import DeviceManager
from magplex.stb import parser
from magplex.utilities.localization import Locale
from magplex.utilities.variables import Environment

stb = Blueprint("stb", __name__)


@stb.route('/<uuid:device_uid>/stb/')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_root(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return Response(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    return Response(parser.build_device_info(user_device.device_uid, domain), mimetype='text/xml')


@stb.route('/<uuid:device_uid>/stb/discover.json')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_discover(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    return jsonify(parser.build_discover(domain))


@stb.route('/<uuid:device_uid>/stb/lineup_status.json')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_lineup_status(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    return jsonify(parser.build_status())


@stb.route('/<uuid:device_uid>/stb/lineup.json')
@authorize_route(auth_method=AuthMethod.API)
def get_stb_lineup(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return Response(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    domain = request.host_url[:-1]
    channel_list = database.get_enabled_channels(g.db_conn, user_device.device_uid)
    return jsonify([parser.build_lineup_channel(channel, domain) for channel in channel_list if channel])


@stb.route('/<uuid:device_uid>/stb/playlist.m3u8')
def get_stb_channel_playlist(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    stream_id = request.args.get('stream_id')
    if stream_id is None:
        return ErrorResponse(Locale.GENERAL_MISSING_ENDPOINT_PARAMETERS, status=HTTPStatus.BAD_REQUEST)

    channel_url = user_device.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to retrieve channel.", status=HTTPStatus.NOT_FOUND)

    # Attempt to get X-Sid header if it exists.
    response = requests.get(channel_url, allow_redirects=True)

    # Pass session header and others if they exist.
    headers = {}
    for key in ['X-Sid', 'User-Agent', 'Referer', 'Origin']:
        if key in response.headers:
            headers[key] = response.headers[key]
    headers = ''.join(f"{k}: {v}\r\n" for k, v in headers.items())

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
            for chunk in iter(lambda: process.stdout.read(64 * 1024), b''):
                yield chunk
        except GeneratorExit:
            process.terminate()  # Client disconnected, terminate process.
        finally:
            try:
                process.wait(timeout=10)  # Wait for the process to properly clean up and close.
            except TimeoutExpired:
                process.kill()
            finally:
                process.stdout.close()

    return Response(
        stream_with_context(generate()),
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

    channels = database.get_enabled_channels(g.db_conn, user_device.device_uid)
    guides = database.get_current_channel_guides(g.db_conn, user_device.device_uid)
    guide = parser.build_channel_guide(channels, guides)
    return Response(guide, mimetype='text/xml')

