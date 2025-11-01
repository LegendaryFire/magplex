import posixpath
from http import HTTPStatus
from urllib.parse import quote, unquote, urlparse, urlunparse

import requests
from flask import Blueprint, Response, request

from magplex.device.device import DeviceManager
from magplex.utilities.localization import ErrorMessage

proxy = Blueprint("proxy", __name__)


@proxy.route('/channels/<int:stream_id>')
def proxy_playlist(stream_id):
    device = DeviceManager.get_device()
    if device is None:
        return Response(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    channel_url = device.get_channel_playlist(stream_id)
    if channel_url is None:
        return Response(ErrorMessage.DEVICE_UNKNOWN_CHANNEL, status=HTTPStatus.NOT_FOUND)
    response = requests.get(channel_url)
    session_uid = response.headers.get('X-Sid', None)
    playlist_content = response.text

    parsed_url = urlparse(channel_url)
    channel_domain =  urlunparse((parsed_url.scheme, parsed_url.netloc, posixpath.dirname(parsed_url.path), "", "", ""))
    proxied_playlist = []
    for line in playlist_content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            absolute_url = f'{channel_domain}/{line}'
            proxied_url = f"/api/proxy/stream.ts?url={quote(absolute_url)}&session_uid={quote(session_uid)}"
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


@proxy.route('/stream.ts')
def proxy_stream():
    url = request.args.get("url")
    if not url:
        return Response(ErrorMessage.GENERAL_MISSING_ENDPOINT_PARAMETERS, HTTPStatus.BAD_REQUEST)
    url = unquote(url)

    session_uid = request.args.get("session")
    headers = {"X-Sid": session_uid}
    r = requests.get(url, headers=headers, stream=True, allow_redirects=True)

    if r.status_code != HTTPStatus.OK:
        return Response(ErrorMessage.DEVICE_STREAM_SEGMENT_FAILED, r.status_code)

    chunk_size = 32 * 1024  # 32KB
    return Response(r.iter_content(chunk_size=chunk_size), headers=r.headers)
