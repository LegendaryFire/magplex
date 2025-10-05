import posixpath
from http import HTTPStatus
from urllib.parse import quote, urlparse, urlunparse

import requests
from flask import Blueprint, Response, current_app, redirect, request

proxy = Blueprint("proxy", __name__)

@proxy.route('/channels/<int:stream_id>')
def proxy_playlist(stream_id):
    channel_url = current_app.stb.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to proxy stream, no channel URL.", status=HTTPStatus.INTERNAL_SERVER_ERROR)
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


@proxy.route('/stream')
def proxy_stream():
    url = request.args.get("url")
    if not url:
        return Response("Missing mandatory URL parameter.", HTTPStatus.BAD_REQUEST)

    r = requests.get(url, stream=True, headers=current_app.stb.headers, cookies=current_app.stb.cookies)
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