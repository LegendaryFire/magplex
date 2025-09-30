from http import HTTPStatus

import requests
from flask import Blueprint, render_template, send_file, stream_with_context, Response, current_app, request
from urllib.parse import urlparse, urljoin, quote, urlunparse
from version import __version__
import posixpath

ui = Blueprint("ui", __name__)

@ui.route('/')
def index():
    return render_template('index.html')

@ui.route('/logs')
def logs():
    try:
        return send_file(f'logs/v{__version__}.log', as_attachment=False)
    except FileNotFoundError:
        return "Could not find log file.", 404


@ui.route('/proxy/channels/<int:channel_id>')
def proxy_playlist(channel_id):
    channel_url = current_app.stb.get_channel_url(channel_id)
    parsed_url = urlparse(channel_url)
    channel_domain =  urlunparse((parsed_url.scheme, parsed_url.netloc, posixpath.dirname(parsed_url.path), "", "", ""))
    response = requests.get(channel_url)

    playlist_content = response.text
    absolute_playlist = []

    for line in playlist_content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            absolute_url = f'{channel_domain}/{line}'
            response = requests.get(absolute_url, allow_redirects=True)
            # Rewrite to go through the proxy_file endpoint
            proxied_url = f"/proxy/stream?url={quote(response.url)}"
            absolute_playlist.append(proxied_url)
        else:
            absolute_playlist.append(line)

    return Response(
        "\n".join(absolute_playlist),
        headers={
            "Content-Type": "application/vnd.apple.mpegurl",
            "Access-Control-Allow-Origin": "*"
        }
    )


@ui.route('/proxy/stream')
def proxy_stream():
    url = request.args.get("url")
    if not url:
        return Response("Missing mandatory URL parameter.", HTTPStatus.BAD_REQUEST)

    r = requests.get(url, stream=True)
    if r.status_code != HTTPStatus.OK:
        return "Failed to fetch stream segment", 502

    # TS segments are usually video/MP2T
    content_type = r.headers.get("Content-Type", "video/MP2T")

    chunk_size = 512 * 1024  # 512KB
    return Response(
        r.iter_content(chunk_size=chunk_size),
        headers={
            "Content-Type": content_type,
            "Access-Control-Allow-Origin": "*"
        }
    )