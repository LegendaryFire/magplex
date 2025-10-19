import logging
from datetime import datetime, timezone
from http import HTTPStatus

from flask import Blueprint, Response, redirect, jsonify, g

from magplex.decorators import login_required
from magplex.utilities import cache
from magplex.utilities.device import DeviceManager
from magplex.utilities.scheduler import TaskManager

device = Blueprint("device", __name__)


@device.route('/channels')
@login_required
def get_channel_list():
    """Gets the channel list from the portal, returns a playlist if supported, otherwise JSON."""
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    channels_list = user_device.get_channel_list()
    genres = user_device.get_genres()
    if genres is None:
        return Response("Unable to get playlist genres.", HTTPStatus.INTERNAL_SERVER_ERROR)

    genre_name_map = {g.get('genre_id'): g.get('genre_name') for g in genres}
    for index, channel in enumerate(channels_list):
        channels_list[index]['genre_name'] = genre_name_map.get(channel.get('genre_id'), "Unknown")

    return jsonify(channels_list)


@device.get('/channels/guides')
@login_required
def get_all_channel_guides():
    user_device = DeviceManager.get_device()
    channel_guide = cache.get_all_channel_guides(g.cache_conn, user_device.id)
    return jsonify(channel_guide)


@device.post('/channels/guides')
@login_required
def refresh_channel_guides():
    scheduler = TaskManager.get_scheduler()
    user_device = DeviceManager.get_device()
    if user_device is None:
        logging.warning(f"Unable to refresh EPG, ensure a device has been added first.")

    job = scheduler.get_job(user_device.id)
    if not job:
        logging.warning(f"Unable to refresh EPG, ensure a device has been added first.")
        return Response(status=HTTPStatus.NOT_FOUND)

    job.modify(next_run_time=datetime.now(timezone.utc))
    logging.info(f"Manually triggered EPG refresh for device {user_device.id}.")
    return Response(status=HTTPStatus.ACCEPTED)


@device.get('/channels/<int:channel_id>/guide')
@login_required
def get_channel_guide(channel_id):
    user_device = DeviceManager.get_device()
    channel_guide = cache.get_channel_guide(g.cache_conn, user_device.id, channel_id)
    return jsonify(channel_guide)


@device.route('/playlists/<int:stream_id>')
@login_required
def get_channel_playlist(stream_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    channel_url = user_device.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to retrieve channel.", status=HTTPStatus.NOT_FOUND)
    return redirect(channel_url, code=HTTPStatus.FOUND)