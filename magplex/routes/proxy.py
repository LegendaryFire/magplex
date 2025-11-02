import base64
import json
import logging
import os
from http import HTTPStatus
from urllib.parse import urljoin

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import requests
from flask import Blueprint, Response, request, stream_with_context

from magplex.device.device import DeviceManager
from magplex.utilities.localization import ErrorMessage

proxy = Blueprint("proxy", __name__)


@proxy.route('/channels/<int:stream_id>')
def proxy_playlist(stream_id):
    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)
    stream_link = user_device.get_channel_playlist(stream_id)
    if stream_link is None:
        return Response(ErrorMessage.DEVICE_UNKNOWN_CHANNEL, status=HTTPStatus.NOT_FOUND)
    response = requests.get(stream_link)
    session_identifier = response.headers.get('X-Sid', None)

    # There are often redirects, which we must follow to get the final link path.
    base_link = urljoin(response.url, './')

    current_playlist = response.text
    proxied_playlist = []
    for line in current_playlist.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            data = {
                'base_link': base_link,
                'segment_path': line,
                'session_identifier': session_identifier
            }
            proxied_url = f"/api/proxy/stream.ts?data={encrypt_data(user_device, data)}"
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
    data = request.args.get("data")
    if not data:
        return Response(ErrorMessage.GENERAL_MISSING_ENDPOINT_PARAMETERS, HTTPStatus.BAD_REQUEST)

    user_device = DeviceManager.get_device()
    if user_device is None:
        return Response(ErrorMessage.DEVICE_UNAVAILABLE, status=HTTPStatus.FORBIDDEN)

    data = decrypt_data(user_device, data)
    if data is None:
        return Response("Invalid encrypted data.", status=HTTPStatus.FORBIDDEN)

    session_identifier = data.get('session_identifier')
    headers = {"X-Sid": session_identifier} if session_identifier else {}

    stream_link = f"{data.get('base_link')}{data.get('segment_path')}"
    logging.error(stream_link)
    r = requests.get(stream_link, headers=headers, stream=True, allow_redirects=True)

    if r.status_code != HTTPStatus.OK:
        return Response(ErrorMessage.DEVICE_STREAM_SEGMENT_FAILED, r.status_code)

    response = Response(stream_with_context(r.iter_content(chunk_size=8192)), status=HTTPStatus.OK,
                        direct_passthrough=True, content_type="video/mp2t")

    response.headers["Cache-Control"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

def encrypt_data(user_device, data: dict) -> str:
    crypto = AESGCM(user_device.get_device_encryption_key())

    # 96-bit random nonce for AES-GCM
    nonce = os.urandom(12)
    plaintext = json.dumps(data).encode()

    ct = crypto.encrypt(nonce, plaintext, None)
    blob = nonce + ct
    return base64.urlsafe_b64encode(blob).decode().rstrip("=")  # URL safe


def decrypt_data(user_device, data: str) -> dict:
    crypto = AESGCM(user_device.get_device_encryption_key())

    # Restore stripped padding.
    data += "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(data)
    nonce, ct = raw[:12], raw[12:]
    plaintext = crypto.decrypt(nonce, ct, None)
    return json.loads(plaintext)