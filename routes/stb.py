import json
import logging
import subprocess
import threading

from flask import Blueprint, Response, current_app, jsonify, request

stb = Blueprint("stb", __name__)


@stb.route('/')
def root():
    domain = request.host_url[:-1]
    return Response(f"""
    <root>
        <URLBase>{domain}</URLBase>
        <specVersion>
        <major>1</major>
        <minor>0</minor>
        </specVersion>
        <device>
            <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
            <friendlyName>Magplex</friendlyName>
            <manufacturer>Silicondust</manufacturer>
            <modelName>HDTC-2US</modelName>
            <modelNumber>HDTC-2US</modelNumber>
            <serialNumber>{current_app.stb.id}</serialNumber>
            <UDN>uuid:2025-10-FBE0-RLST64</UDN>
        </device>
    </root>
    """, mimetype='text/xml')


@stb.route('/discover.json')
def discover():
    domain = request.host_url[:-1]
    return jsonify({
        "BaseURL": domain,
        "DeviceAuth": "Magplex",
        "DeviceID": "2025-10-FBE0-RLST64",
        "FirmwareName": "bin_1.2",
        "FirmwareVersion": "1.2",
        "FriendlyName": "Magplex",
        "LineupURL": f"{domain}/stb/lineup.json",
        "Manufacturer": "LegendaryFire",
        "ModelNumber": "1.2",
        "TunerCount": 1
    })

@stb.route('/lineup_status.json')
def lineup_status():
    return jsonify({
        "ScanInProgress": 0,
        "ScanPossible": 1,
        "Source": "Cable",
        "Lineup": "Complete"
    })

@stb.route('/lineup.json')
def lineup():
    domain = request.host_url[:-1]
    channel_list = current_app.stb.get_channel_list()
    channel_lineup = []
    for channel in channel_list:
        channel_lineup.append({
            "GuideName": json.dumps(channel.get('channel_name'), ensure_ascii=True),
            "GuideNumber": channel.get('channel_id'),
            "URL": f"{domain}/stb/stream/{channel.get('stream_id')}"
        })

    return jsonify(channel_lineup)


@stb.route('/stream/<int:stream_id>')
def buffered_stream(stream_id):
    domain = request.host_url[:-1]
    ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
        "-allowed_extensions", "ALL",
        "-i", f"{domain}/proxy/channels/{stream_id}",
        "-c", "copy",
        "-f", "mpegts",
        "pipe:1"
    ]
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def log_errors():
        for line in iter(process.stderr.readline, b""):
            logging.error(line.decode(errors="ignore").strip())
    threading.Thread(target=log_errors, daemon=True).start()

    def generate():
        try:
            while True:
                data = process.stdout.read(64 * 1024)  # 64KB
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(
        generate(),
        headers={
            "Content-Type": "video/mp2t",
            "Access-Control-Allow-Origin": "*"
        }
    )
