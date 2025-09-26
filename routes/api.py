from flask import Blueprint, redirect, request, Response, jsonify
from flask import current_app
from utilities import parser, cache_utils
from utilities.media import MimeType
from http import HTTPStatus

api = Blueprint("api", __name__)
@api.route('/channels/<channel_id>')
def channel(channel_id):
    channel_url = current_app.stb.get_channel_url(channel_id)
    return redirect(channel_url, code=HTTPStatus.FOUND)

@api.route('/channels/list')
def channel_list():
    channels = current_app.stb.get_channel_list()
    best_match = request.accept_mimetypes.best_match(MimeType.all_types())

    if best_match in MimeType.m3u8_types():
        domain = request.host_url[:-1]
        playlist = parser.build_playlist(channels, domain)
        return Response(playlist, mimetype=best_match)

    # Default to JSON
    return jsonify(channels)

@api.route('/channels/guide.xml')
def channel_guide():
    guide = cache_utils.get_channel_guide()
    return Response(guide, mimetype='text/xml')