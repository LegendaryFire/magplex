from http import HTTPStatus

from flask import Blueprint, Response, current_app, jsonify, redirect

from version import version

api = Blueprint("api", __name__)
@api.route('/channels/<int:stream_id>')
def get_channel_playlist(stream_id):
    channel_url = current_app.stb.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to retrieve channel.", status=HTTPStatus.NOT_FOUND)
    return redirect(channel_url, code=HTTPStatus.FOUND)


@api.route('/channels/list')
def get_channel_list():
    """Gets the channel list from the portal, returns a playlist if supported, otherwise JSON."""
    channels = current_app.stb.get_channel_list()
    genres = current_app.stb.get_genres()
    if genres is None:
        return Response("Unable to get playlist genres.", HTTPStatus.INTERNAL_SERVER_ERROR)

    genre_name_map = {g.get('genre_id'): g.get('genre_name') for g in genres}
    for index, channel in enumerate(channels):
        channels[index]['genre_name'] = genre_name_map.get(channel.get('genre_id'), "Unknown")

    return jsonify(channels)

@api.route('/about')
def get_about():
    return jsonify({
        'version': version,
    })