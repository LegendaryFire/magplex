import posixpath
from http import HTTPStatus
from urllib.parse import quote, urlparse, urlunparse, unquote

import requests
from flask import Blueprint, Response, current_app, redirect, request

proxy = Blueprint("proxy", __name__)

@proxy.route('/channels/<int:stream_id>')
def proxy_playlist(stream_id):
    channel_url = current_app.stb.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response("Unable to proxy stream, no channel URL.", status=HTTPStatus.INTERNAL_SERVER_ERROR)
    response = requests.get(channel_url)
    session_uid = response.headers.get('X-Sid', None)
    playlist_content = response.text

    parsed_url = urlparse(channel_url)
    domain = request.host_url[:-1]
    channel_domain =  urlunparse((parsed_url.scheme, parsed_url.netloc, posixpath.dirname(parsed_url.path), "", "", ""))
    proxied_playlist = []
    for line in playlist_content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            absolute_url = f'{channel_domain}/{line}'
            proxied_url = f"/proxy/stream?url={quote(absolute_url)}&session_uid={quote(session_uid)}"
            proxied_playlist.append(proxied_url)
        else:
            proxied_playlist.append(line)

    return Response(
        "\n".join(proxied_playlist),
        headers={
            "Content-Type": "application/vnd.apple.mpegurl",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        }
    )


@proxy.route('/stream')
def proxy_stream():
    url = request.args.get("url")
    if not url:
        return Response("Missing mandatory URL parameter.", HTTPStatus.BAD_REQUEST)
    url = unquote(url)

    session_uid = request.args.get("session")
    headers = {"X-Sid": session_uid}
    r = requests.get(url, headers=headers, stream=True, allow_redirects=True)

    if r.status_code != HTTPStatus.OK:
        return Response("Failed to fetch stream segment.", r.status_code)

    chunk_size = 64 * 1024  # 64KB
    return Response(r.iter_content(chunk_size=chunk_size), headers=r.headers)
