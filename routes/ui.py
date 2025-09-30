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
        return Response("Could not find log file.", HTTPStatus.NOT_FOUND)


@ui.route('/proxy/channels/<int:channel_id>')
def proxy_playlist(channel_id):
    channel_url = current_app.stb.get_channel_url(channel_id)
    response = requests.get(channel_url)
    playlist_content = response.text

    parsed_url = urlparse(channel_url)
    channel_domain =  urlunparse((parsed_url.scheme, parsed_url.netloc, posixpath.dirname(parsed_url.path), "", "", ""))
    proxied_playlist = []
    for line in playlist_content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            absolute_url = f'{channel_domain}/{line}'
            response = requests.get(absolute_url, allow_redirects=True)
            proxied_url = f"/proxy/stream?url={quote(response.url)}"
            proxied_playlist.append(proxied_url)
        else:
            proxied_playlist.append(line)

    return Response(
        "\n".join(proxied_playlist),
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
        return Response("Failed to fetch stream segment.", r.status_code)

    content_type = r.headers.get("Content-Type")
    chunk_size = 512 * 1024  # 512KB
    return Response(
        r.iter_content(chunk_size=chunk_size),
        headers={
            "Content-Type": content_type,
            "Access-Control-Allow-Origin": "*"
        }
    )