import logging
from collections import defaultdict
from datetime import datetime, timezone
from enum import StrEnum
from http import HTTPStatus
from urllib.parse import urljoin

import requests
from flask import Blueprint, Response, g, jsonify, redirect, request, stream_with_context

from magplex import PostgresConnection
from magplex.decorators import login_required
from magplex.device import database
from magplex.device.device import DeviceManager
from magplex.utilities.localization import ErrorMessage
from magplex.utilities.error import ErrorResponse
from magplex.utilities.scheduler import TaskManager

device = Blueprint("device", __name__)

class ChannelState(StrEnum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'


@device.get('/genres')
@login_required
def get_genres():
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    channel_state = request.args.get('state', '').lower()
    if channel_state == ChannelState.ENABLED:
        genres = database.get_enabled_channel_genres(g.db_conn, user_device.device_uid)
    elif channel_state == ChannelState.DISABLED:
        genres = database.get_disabled_channel_genres(g.db_conn, user_device.device_uid)
    else:
        genres = database.get_all_genres(g.db_conn, user_device.device_uid)
    return jsonify(genres)


@device.get('/channels')
@login_required
def get_channels():
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    channel_state = request.args.get('state', '').lower()
    if channel_state == ChannelState.ENABLED:
        enabled_channels = database.get_enabled_channels(g.db_conn, user_device.device_uid)
        return jsonify(enabled_channels)
    elif channel_state == ChannelState.DISABLED:
        disabled_channels = database.get_disabled_channels(g.db_conn, user_device.device_uid)
        return jsonify(disabled_channels)
    else:
        all_channels = database.get_all_channels(g.db_conn, user_device.device_uid)
        return jsonify(all_channels)


@device.post('/channels')
@login_required
def update_channels():
    scheduler = TaskManager.get_scheduler()
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    job = scheduler.get_job(f'{user_device.device_uid}:save_channels')
    if not job:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    job.modify(next_run_time=datetime.now(timezone.utc))
    logging.info(f"Manually triggered channel list refresh for device {user_device.device_uid}.")
    return Response(status=HTTPStatus.ACCEPTED)


@device.get('/channels/guides')
@login_required
def get_channel_guides():
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    epg = database.get_current_channel_guides(g.db_conn, user_device.device_uid)
    guide_map = defaultdict(list)
    for guide in epg:
        guide_map[guide.channel_id].append(guide)
    return jsonify(guide_map)


@device.get('/channels/<int:channel_id>/guide')
@login_required
def get_channel_guide(channel_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    channel_guide = database.get_channel_guide(g.db_conn, user_device.device_uid, channel_id)
    return jsonify(channel_guide)


@device.post('/channels/guides')
@login_required
def refresh_channel_guides():
    scheduler = TaskManager.get_scheduler()
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    job = scheduler.get_job(f'{user_device.device_uid}:save_channel_guides')
    if not job:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)

    job.modify(next_run_time=datetime.now(timezone.utc))
    logging.info(ErrorMessage.TASK_CHANNEL_GUIDE_TRIGGERED)
    return Response(status=HTTPStatus.ACCEPTED)


@device.post('/channels/toggle')
@login_required
def toggle_channels():
    channels_enabled = request.json.get('channels_enabled')
    if channels_enabled is None:
        return ErrorResponse(ErrorMessage.GENERAL_MISSING_ENDPOINT_PARAMETERS)
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    database.update_channels_enabled(g.db_conn, user_device.device_uid, channels_enabled)
    return Response(status=HTTPStatus.OK)


@device.post('/channels/<int:channel_id>/toggle')
@login_required
def toggle_channel(channel_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    database.toggle_channel_enabled(g.db_conn, user_device.device_uid, channel_id)
    return Response(status=HTTPStatus.OK)


@device.route('/channels/<int:channel_id>')
def stream_playlist(channel_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    channel = database.get_channel(g.db_conn, user_device.device_uid, channel_id)
    if channel is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)
    stream_link = user_device.get_channel_playlist(channel.stream_id)
    if stream_link is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNKNOWN_STREAM, HTTPStatus.NOT_FOUND)

    return redirect(stream_link, code=HTTPStatus.FOUND)


@device.route('/channels/<int:channel_id>/proxy')
def proxy_playlist(channel_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    channel = database.get_channel(g.db_conn, user_device.device_uid, channel_id)

    if channel is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)
    stream_link = user_device.get_channel_playlist(channel.stream_id)

    if stream_link is None:
        return Response(ErrorMessage.DEVICE_UNKNOWN_CHANNEL, status=HTTPStatus.NOT_FOUND)
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
            proxied_url = f"/api/device/channels/{channel.channel_id}/proxy/stream.ts?data={user_device.encrypt_data(data)}"
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


@device.route('/channels/<int:channel_id>/proxy/stream.ts')
def proxy_stream(channel_id):
    data = request.args.get("data")
    if not data:
        return ErrorResponse(ErrorMessage.GENERAL_MISSING_ENDPOINT_PARAMETERS, HTTPStatus.BAD_REQUEST)

    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    channel = database.get_channel(g.db_conn, user_device.device_uid, channel_id)
    if channel is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)

    data = user_device.decrypt_data(data)
    if data is None:
        return ErrorResponse(ErrorMessage.DEVICE_INVALID_DECRYPTED_DATA, status=HTTPStatus.FORBIDDEN)

    stream_id = data.get('stream_id')
    if stream_id != channel.stream_id:
        return ErrorResponse(ErrorMessage.DEVICE_CHANNEL_STREAM_MISMATCH, status=HTTPStatus.NOT_FOUND)

    session_identifier = data.get('session_identifier')
    headers = {"X-Sid": session_identifier} if session_identifier else {}

    stream_link = f"{data.get('base_link')}{data.get('segment_path')}"
    logging.error(stream_link)
    r = requests.get(stream_link, headers=headers, stream=True, allow_redirects=True)

    if r.status_code != HTTPStatus.OK:
        return ErrorResponse(ErrorMessage.DEVICE_STREAM_SEGMENT_FAILED, HTTPStatus(r.status_code))

    response = Response(stream_with_context(r.iter_content(chunk_size=8192)), status=HTTPStatus.OK,
                        direct_passthrough=True, content_type="video/mp2t")

    response.headers["Cache-Control"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
