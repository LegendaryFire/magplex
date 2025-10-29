import logging
from datetime import datetime, timezone
from enum import StrEnum
from http import HTTPStatus

from flask import Blueprint, Response, redirect, jsonify, g, request

from magplex.device import database, cache
from magplex.decorators import login_required
from magplex.device.device import DeviceManager
from magplex.utilities.error import ErrorResponse
from magplex.utilities.scheduler import TaskManager

device = Blueprint("device", __name__)

class ChannelState(StrEnum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'


@device.route('/channels')
@login_required
def get_channels():
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)

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


@device.get('/channels/guides')
@login_required
def get_all_channel_guides():
    user_device = DeviceManager.get_device()
    channel_guide = cache.get_all_channel_guides(g.cache_conn, user_device.device_uid)
    return jsonify(channel_guide)


@device.post('/channels/guides')
@login_required
def refresh_channel_guides():
    scheduler = TaskManager.get_scheduler()
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse("Unable to refresh EPG, ensure a device has been added first.", HTTPStatus.INTERNAL_SERVER_ERROR)
    job = scheduler.get_job(user_device.device_uid)
    if not job:
        return ErrorResponse("Unable to refresh EPG, ensure a device has been added first.", HTTPStatus.INTERNAL_SERVER_ERROR)

    job.modify(next_run_time=datetime.now(timezone.utc))
    logging.info(f"Manually triggered EPG refresh for device {user_device.device_uid}.")
    return Response(status=HTTPStatus.ACCEPTED)


@device.post('/channels/toggle')
@login_required
def toggle_channels():
    channels_enabled = request.json.get('channels_enabled')
    if channels_enabled is None:
        return ErrorResponse("Missing mandatory data.")
    user_device = DeviceManager.get_device()
    database.update_channels_enabled(g.db_conn, user_device.device_uid, channels_enabled)
    cache.expire_channels(g.cache_conn, user_device.device_uid)
    return Response(status=HTTPStatus.OK)


@device.post('/channels/<int:channel_id>/toggle')
@login_required
def toggle_channel(channel_id):
    user_device = DeviceManager.get_device()
    database.toggle_channel_enabled(g.db_conn, user_device.device_uid, channel_id)
    cache.expire_channels(g.cache_conn, user_device.device_uid)
    return Response(status=HTTPStatus.OK)


@device.get('/channels/<int:channel_id>/guide')
@login_required
def get_channel_guide(channel_id):
    user_device = DeviceManager.get_device()
    channel_guide = cache.get_channel_guide(g.cache_conn, user_device.device_uid, channel_id)
    return jsonify(channel_guide)


@device.route('/playlists/<int:stream_id>')
@login_required
def get_channel_playlist(stream_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return ErrorResponse('Unable to get device. Please check configuration', HTTPStatus.FORBIDDEN)
    channel_url = user_device.get_channel_playlist(stream_id)
    if channel_url is None:
        return ErrorResponse('Unable to retrieve channel.', HTTPStatus.NOT_FOUND)

    return redirect(channel_url, code=HTTPStatus.FOUND)