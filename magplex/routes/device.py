import logging
from collections import defaultdict
from datetime import datetime, timezone
from http import HTTPStatus
from urllib.parse import urljoin

import requests
from flask import Blueprint, Response, g, jsonify, redirect, request, stream_with_context

from magplex.decorators import authorize_route, AuthMethod
from magplex.device import database
from magplex.device.manager import DeviceManager
from magplex.utilities import sanitizer
from magplex.utilities.error import ErrorResponse
from magplex.utilities.localization import Locale
from magplex.utilities.scheduler import TaskManager

device = Blueprint("device", __name__)


@device.get('/<uuid:device_uid>/genres')
@authorize_route(auth_method=AuthMethod.ALL)
def get_genres(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    kwargs = {}
    if 'channel_enabled' in request.args:
        kwargs.update({'channel_enabled': sanitizer.sanitize_bool(request.args.get('channel_enabled'))})
    if 'channel_stale' in request.args:
        kwargs.update({'channel_stale': sanitizer.sanitize_bool(request.args.get('channel_stale'))})
    genres = database.get_all_genres(g.db_conn, user_device.device_uid, **kwargs)
    return jsonify(genres)


@device.get('/<uuid:device_uid>/channels')
@authorize_route(auth_method=AuthMethod.ALL)
def get_channels(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    kwargs = {}
    if 'channel_enabled' in request.args:
        kwargs.update({'channel_enabled': sanitizer.sanitize_bool(request.args.get('channel_enabled'))})
    if 'channel_stale' in request.args:
        kwargs.update({'channel_stale': sanitizer.sanitize_bool(request.args.get('channel_stale'))})
    if 'genre_id' in request.args:
        kwargs.update({'genre_id': sanitizer.sanitize_int(request.args.get('genre_id'))})
    if 'q' in request.args:
        kwargs.update({'q': sanitizer.sanitize_string(request.args.get('q'))})
    channels = database.get_channels(g.db_conn, user_device.device_uid, **kwargs)
    return jsonify(channels)



@device.post('/<uuid:device_uid>/channels')
@authorize_route(auth_method=AuthMethod.ALL)
def update_channels(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    data = request.get_json()
    kwargs = {}
    if 'channel_enabled' in data:
        kwargs.update({'channel_enabled': sanitizer.sanitize_bool(data.get('channel_enabled'))})
    if 'channel_stale' in data:
        kwargs.update({'channel_stale': sanitizer.sanitize_bool(data.get('channel_stale'))})
    database.update_channels(g.db_conn, user_device.device_uid, **kwargs)
    return Response(status=HTTPStatus.OK)


@device.post('/<uuid:device_uid>/channels/sync')
@authorize_route(auth_method=AuthMethod.ALL)
def sync_channels(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    scheduler = TaskManager.get_scheduler()
    job = scheduler.get_job(f'{user_device.device_uid}:save_channels')
    if not job:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    job.modify(next_run_time=datetime.now(timezone.utc))
    return Response(status=HTTPStatus.OK)


@device.get('/<uuid:device_uid>/channels/<int:channel_id>')
@authorize_route(auth_method=AuthMethod.ALL)
def get_channel_playlist(device_uid, channel_id):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    channel = database.get_channel(g.db_conn, user_device.device_uid, channel_id)
    if channel is None:
        return ErrorResponse(Locale.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)

    stream_link = user_device.get_channel_playlist(channel.stream_id)
    if stream_link is None:
        return ErrorResponse(Locale.DEVICE_UNKNOWN_STREAM, HTTPStatus.NOT_FOUND)

    return redirect(stream_link, code=HTTPStatus.FOUND)


@device.post('/<uuid:device_uid>/channels/<int:channel_id>')
@authorize_route(auth_method=AuthMethod.ALL)
def update_channel(device_uid, channel_id):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    channel = database.get_channel(g.db_conn, user_device.device_uid, channel_id)
    if channel is None:
        return ErrorResponse(Locale.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)

    data = request.get_json()
    kwargs = {}
    if 'channel_name' in data:
        kwargs.update({'channel_name': sanitizer.sanitize_string(data.get('channel_name'), max_length=128)})
    if 'channel_hd' in data:
        kwargs.update({'channel_hd': sanitizer.sanitize_bool(data.get('channel_hd'))})
    if 'channel_enabled' in data:
        kwargs.update({'channel_enabled': sanitizer.sanitize_bool(data.get('channel_enabled'))})
    database.update_channel(g.db_conn, user_device.device_uid, channel_id, **kwargs)

    return Response(status=HTTPStatus.OK)


@device.get('/<uuid:device_uid>/channels/guides')
@authorize_route(auth_method=AuthMethod.ALL)
def get_channel_guides(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    epg = database.get_current_channel_guides(g.db_conn, user_device.device_uid)
    guide_map = defaultdict(list)
    for guide in epg:
        guide_map[guide.channel_id].append(guide)
    return jsonify(guide_map)


@device.post('/<uuid:device_uid>/channels/guides/sync')
@authorize_route(auth_method=AuthMethod.ALL)
def sync_channel_guides(device_uid):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    scheduler = TaskManager.get_scheduler()
    job = scheduler.get_job(f'{user_device.device_uid}:save_channel_guides')
    if not job:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    job.modify(next_run_time=datetime.now(timezone.utc))
    logging.info(Locale.TASK_CHANNEL_GUIDE_TRIGGERED)
    return Response(status=HTTPStatus.ACCEPTED)


@device.get('/<uuid:device_uid>/channels/<int:channel_id>/guide')
@authorize_route(auth_method=AuthMethod.ALL)
def get_channel_guide(device_uid, channel_id):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    channel_guide = database.get_channel_guide(g.db_conn, user_device.device_uid, channel_id)
    return jsonify(channel_guide)


@device.get('/<uuid:device_uid>/channels/<int:channel_id>/proxy')
@authorize_route(auth_method=AuthMethod.ALL)
def proxy_playlist(device_uid, channel_id):
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None or user_device.device_uid != str(device_uid):
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    channel = database.get_channel(g.db_conn, user_device.device_uid, channel_id)
    if channel is None:
        return ErrorResponse(Locale.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)
    stream_link = user_device.get_channel_playlist(channel.stream_id)

    if stream_link is None:
        return ErrorResponse(Locale.DEVICE_UNKNOWN_CHANNEL, status=HTTPStatus.NOT_FOUND)
    response = requests.get(stream_link)
    session_identifier = response.headers.get('X-Sid', None)

    # There are often redirects, which we must follow to get the final link path.
    base_link = urljoin(response.url, './')

    current_playlist = response.text
    proxied_playlist = []
    for line in current_playlist.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            data = {
                'stream_id': channel.stream_id,
                'base_link': base_link,
                'segment_path': line,
                'session_identifier': session_identifier
            }
            proxied_url = f"/api/devices/{device_uid}/channels/{channel.channel_id}/proxy/stream.ts?data={user_device.encrypt_data(data)}"
            proxied_playlist.append(proxied_url)
        else:
            proxied_playlist.append(line)

    return Response(
        "\n".join(proxied_playlist),
        headers={
            "Content-Type": "application/vnd.apple.mpegurl",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        }
    )


@device.get('/<uuid:device_uid>/channels/<int:channel_id>/proxy/stream.ts')
def proxy_stream(device_uid, channel_id):
    data = request.args.get("data")
    if not data:
        return ErrorResponse(Locale.GENERAL_MISSING_ENDPOINT_PARAMETERS, HTTPStatus.BAD_REQUEST)

    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        return ErrorResponse(Locale.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    channel = database.get_channel(g.db_conn, user_device.device_uid, channel_id)
    if channel is None:
        return ErrorResponse(Locale.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)

    data = user_device.decrypt_data(data)
    if data is None:
        return ErrorResponse(Locale.DEVICE_INVALID_DECRYPTED_DATA, status=HTTPStatus.FORBIDDEN)

    stream_id = data.get('stream_id')
    if stream_id != channel.stream_id:
        return ErrorResponse(Locale.DEVICE_CHANNEL_STREAM_MISMATCH, status=HTTPStatus.NOT_FOUND)

    session_identifier = data.get('session_identifier')
    headers = {"X-Sid": session_identifier} if session_identifier else {}

    stream_link = f"{data.get('base_link')}{data.get('segment_path')}"
    logging.error(stream_link)
    r = requests.get(stream_link, headers=headers, stream=True, allow_redirects=True)

    if r.status_code != HTTPStatus.OK:
        return ErrorResponse(Locale.DEVICE_STREAM_SEGMENT_FAILED, HTTPStatus(r.status_code))

    response = Response(stream_with_context(r.iter_content(chunk_size=8192)), status=HTTPStatus.OK,
                        direct_passthrough=True, content_type="video/mp2t")

    response.headers["Cache-Control"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
