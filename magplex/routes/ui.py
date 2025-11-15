import logging
import time
from http import HTTPStatus

from flask import Blueprint, Response, g, jsonify, make_response, render_template, request

import version
from magplex import RedisPool
from magplex.decorators import AuthMethod, authorize_route
from magplex.device import database
from magplex.utilities.error import ErrorResponse
from magplex.utilities.logs import REDIS_BUFFER_CHANNEL, REDIS_LOG_BUFFER

ui = Blueprint("ui", __name__)


@ui.get('/login')
def login_page():
    return render_template('login.html')


@ui.route('/')
@authorize_route(auth_method=AuthMethod.SESSION, force_redirect=True)
def index():
    return render_template('index.html')


@ui.route('/logs')
@authorize_route(auth_method=AuthMethod.SESSION)
def logs():
    heartbeat_interval = 15
    def event_stream():
        cache_conn = RedisPool.get_connection()
        pubsub = cache_conn.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(REDIS_BUFFER_CHANNEL)

        history = cache_conn.lrange(REDIS_LOG_BUFFER, 0, -1)
        for entry in reversed(history):
            if isinstance(entry, bytes):
                entry = entry.decode()
            for line in entry.split("\n"):
                if line.strip():
                    yield f"data: {line}\n\n".encode("utf-8")

        last_heartbeat = time.time()
        while True:
            msg = pubsub.get_message(timeout=0.5)
            if msg and msg["type"] == "message":
                data = msg["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                for line in data.split("\n"):
                    if line.strip():
                        yield f"data: {line}\n\n".encode("utf-8")
            now = time.time()
            if now - last_heartbeat >= heartbeat_interval:
                yield b": heartbeat\n\n"
                last_heartbeat = now

    return Response(event_stream(), mimetype="text/event-stream", direct_passthrough=True,
                    headers={"Cache-Control": "no-cache"})


@ui.route('/about')
@authorize_route(auth_method=AuthMethod.SESSION)
def get_about():
    return jsonify({
        'version': version.version,
        'build_date': getattr(version, "build_date", "Unknown")
    })


@ui.get("/stalker")
def portal_root():
    return make_response(render_template('portal.html'), 200, {
        "Content-Type": "text/html; charset=utf-8",
        "Connection": "Keep-Alive"
    })


@ui.post("/stalker")
def get_ids():
    payload = request.get_json()
    mac_address = payload.get('mac_address')
    device_id1 = payload.get('device_id1')
    device_id2 = payload.get('device_id2')

    if device_id1 is None or device_id2 is None or mac_address is None:
        return ErrorResponse("Unable to get device information.", HTTPStatus.BAD_REQUEST)

    database.update_device_id(g.db_conn, mac_address, device_id1, device_id2)
    logging.info(f"Device ID updated for MAC address: {mac_address}.")
    return Response(status=200)