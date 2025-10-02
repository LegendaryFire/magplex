from flask import Blueprint, redirect, request, Response, jsonify
from flask import current_app
from utilities import parser, cache
from utilities.media import MimeType
from http import HTTPStatus

api = Blueprint("api", __name__)
@api.route('/channels/<channel_id>')
def get_channel(channel_id):
    channel_url = current_app.stb.get_channel(channel_id)
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
    best_match = request.accept_mimetypes.best_match(MimeType.all_types())

    if best_match in MimeType.m3u8_types():
        domain = request.host_url[:-1]
        playlist = parser.build_playlist(channels, domain)
        return Response(playlist, mimetype=best_match)

    # Default to JSON
    return jsonify(channels)


@api.route('/channels/guide.xml')
def get_channel_guide():
    data = current_app.stb.get_channel_guide()
    guide = parser.build_channel_guide(data.get('channels'), data.get('channel_guides'))
    return Response(guide, mimetype='text/xml')
