from xml.sax.saxutils import escape

from lxml import etree

from version import version


def build_playlist(channels, genres, base_url):
    playlist = '#EXTM3U\n'
    playlist += '#EXT-X-VERSION:3\n\n'
    for c in channels:
        genre_name = None
        for g in genres:
            if g.genre_id == c.genre_id:
                genre_name = g.genre_name
        if genre_name is None:
            continue
        playlist += f'#EXTINF:-1 tvg-id="{c.channel_id}" tvg-name="{c.channel_name}" group-title="{genre_name}",{c.channel_name}\n'
        playlist += f'{base_url}/api/channels/{c.stream_id}\n\n'
    return playlist


def build_channel_guide(channels, guides):
    tv = etree.Element("tv", attrib={
        "generator-info-name": "XMLTV",
        "source-info-name": f"MagPlex v{version}",
    })

    channel_map = {}
    for c in channels:
        channel_elem = etree.SubElement(tv, "channel", id=str(c.channel_id))
        etree.SubElement(channel_elem, "display-name").text = c.channel_name
        channel_map.update({c.channel_id: c.channel_name})

    for g in guides:
        channel_name = channel_map.get(g.channel_id)
        if channel_name is None:
            continue
        start_timestamp = g.start_timestamp.strftime('%Y%m%d%H%M%S')
        end_timestamp = g.end_timestamp.strftime('%Y%m%d%H%M%S')
        guide_elem = etree.SubElement(tv, "programme", channel=str(g.channel_id), start=start_timestamp, stop=end_timestamp)
        etree.SubElement(guide_elem, "title").text = g.title
        if g.description:
            etree.SubElement(guide_elem, "desc").text = g.description
        for category in g.categories:
            etree.SubElement(guide_elem, "category").text = category

    xml = etree.tostring(tv, pretty_print=True, encoding="UTF-8", xml_declaration=False).decode("UTF-8")

    # Combine XML declaration, DOCTYPE, and XML content in the correct order
    declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    doctype = '<!DOCTYPE tv SYSTEM "xmltv.dtd">'
    return f'{declaration}\n{doctype}\n{xml}'


def build_device_info(device_uid, domain):
    xml = f"""
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
            <serialNumber>{device_uid}</serialNumber>
            <UDN>uuid:2025-10-FBE0-RLST64</UDN>
        </device>
    </root>
    """
    return xml


def build_discover(domain):
    return {
        "BaseURL": domain,
        "DeviceAuth": "Magplex",
        "DeviceID": "2025-10-FBE0-RLST64",
        "FirmwareName": "bin_1.2",
        "FirmwareVersion": "1.2",
        "FriendlyName": "Magplex",
        "LineupURL": f"{domain}/lineup.json",
        "Manufacturer": "LegendaryFire",
        "ModelNumber": "1.2",
        "TunerCount": 1
    }

def build_status():
    return {
        "ScanInProgress": 0,
        "ScanPossible": 1,
        "Source": "Cable",
        "Lineup": "Complete"
    }


def build_lineup_channel(channel, domain):
    return {
        'GuideName': channel.channel_name,
        'GuideNumber': f'{channel.channel_id}',
        'URL': f'{domain}/playlist.m3u8?stream_id={channel.stream_id}'
    }
