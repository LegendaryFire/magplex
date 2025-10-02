from datetime import timezone, datetime
from xml.sax.saxutils import escape
from lxml import etree
from itertools import chain

def build_playlist(channels, base_url):
    playlist = '#EXTM3U\n'
    playlist += '#EXT-X-VERSION:3\n\n'
    for channel in channels:
        channel_id = channel.get('channel_id')
        channel_name = channel.get('channel_name')
        genre_name = channel.get('genre_name')
        playlist += f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" group-title="{genre_name}",{channel_name}\n'
        playlist += f'{base_url}/channel/{channel.get('stream_id')}\n\n'
    return playlist


def build_channel_guide(channels, guides):
    tv = etree.Element(
        "tv",
        attrib={
            "generator-info-name": "XMLTV",
            "source-info-name": "MagPlex by Tristan Balon",
        }
    )
    for channel in channels:
        channel_elem = etree.SubElement(tv, "channel", id=channel.get('channel_id'))
        etree.SubElement(channel_elem, "display-name").text = escape(channel.get('channel_name'))

    guides = list(chain.from_iterable(guides))
    for guide in guides:
        start = datetime.fromtimestamp(int(guide.get('start_timestamp')), tz=timezone.utc).strftime('%Y%m%d%H%M%S')
        stop = datetime.fromtimestamp(int(guide.get('stop_timestamp')), tz=timezone.utc).strftime('%Y%m%d%H%M%S')
        guide_elem = etree.SubElement(tv, "programme", channel=guide.get('channel_id'), start=start, stop=stop)
        etree.SubElement(guide_elem, "title").text = escape(guide.get('channel_name'))
        if guide.get('channel_description'):
            etree.SubElement(guide_elem, "desc").text = escape(guide.get('channel_description'))
        for category in guide.get('categories', []):
            etree.SubElement(guide_elem, "category").text = escape(category)

    xml_str = etree.tostring(tv, pretty_print=True, encoding="UTF-8", xml_declaration=False).decode("UTF-8")
    # Combine XML declaration, DOCTYPE, and XML content in the correct order
    doctype = '<!DOCTYPE tv SYSTEM "xmltv.dtd">'
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    channel_guide = f'{xml_declaration}\n{doctype}\n{xml_str}'
    return channel_guide
