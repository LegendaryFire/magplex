import logging
from datetime import datetime, timezone
from http import HTTPStatus

from flask import Blueprint, Response, redirect, jsonify, g, request

from magplex.device import database
from magplex.decorators import login_required
from magplex.utilities import cache
from magplex.device.device import DeviceManager
from magplex.utilities.error import ErrorResponse
from magplex.utilities.scheduler import TaskManager

device = Blueprint("device", __name__)


@device.route('/channels')
@login_required
def get_channels():
    filter_channels = request.args.get("filter", None)
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    channels_list = user_device.get_channels(enabled=filter_channels)
    return jsonify(channels_list)


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

@device.post('/channels/<int:channel_id>/enable')
@login_required
def enable_channel(channel_id):
    user_device = DeviceManager.get_device()
    database.update_channel_status(g.db_conn, user_device.device_uid, channel_id, True)
    return Response(status=HTTPStatus.OK)

@device.post('/channels/<int:channel_id>/disable')
@login_required
def disable_channel(channel_id):
    user_device = DeviceManager.get_device()
    database.update_channel_status(g.db_conn, user_device.device_uid, channel_id, False)
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