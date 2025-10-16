from http import HTTPStatus

from flask import Blueprint, Response, jsonify, redirect

from magplex.utilities.device import DeviceManager

channels = Blueprint("channels", __name__)

@channels.route('/<int:stream_id>')
def get_channel_playlist(stream_id):
    device = DeviceManager.get_device()
    if device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    channel_url = device.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to retrieve channel.", status=HTTPStatus.NOT_FOUND)
    return redirect(channel_url, code=HTTPStatus.FOUND)


@channels.route('/list')
def get_channel_list():
    """Gets the channel list from the portal, returns a playlist if supported, otherwise JSON."""
    device = DeviceManager.get_device()
    if device is None:
        return Response("Unable to get device. Please check configuration.", status=HTTPStatus.FORBIDDEN)
    channels_list = device.get_channel_list()
    genres = device.get_genres()
    if genres is None:
        return Response("Unable to get playlist genres.", HTTPStatus.INTERNAL_SERVER_ERROR)

    genre_name_map = {g.get('genre_id'): g.get('genre_name') for g in genres}
    for index, channel in enumerate(channels_list):
        channels_list[index]['genre_name'] = genre_name_map.get(channel.get('genre_id'), "Unknown")

    return jsonify(channels_list)