import logging
from collections import defaultdict
from datetime import datetime, timezone
from enum import StrEnum
from http import HTTPStatus

from flask import Blueprint, Response, g, jsonify, redirect, request

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
    logging.info(f"Manually triggered channel guide refresh for device {user_device.device_uid}.")
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


@device.route('/channels/<int:stream_id>')
def stream_playlist(stream_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNAVAILABLE, HTTPStatus.FORBIDDEN)
    channel_url = user_device.get_channel_playlist(stream_id)
    if channel_url is None:
        return ErrorResponse(ErrorMessage.DEVICE_UNKNOWN_CHANNEL, HTTPStatus.NOT_FOUND)

    return redirect(channel_url, code=HTTPStatus.FOUND)