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


def build_channel_guide(channels, guides, timezone):
    tv = etree.Element(
        "tv",
        attrib={
            "generator-info-name": "XMLTV",
            "source-info-name": f"MagPlex v{version}",
        }
    )

    channel_map = {}
    for c in channels:
        channel_elem = etree.SubElement(tv, "channel", id=str(c.channel_id))
        etree.SubElement(channel_elem, "display-name").text = escape(c.channel_name)
        channel_map.update({c.channel_id: c.channel_name})

    for g in guides:
        channel_name = channel_map.get(g.channel_id)
        if channel_name is None:
            continue
        start_timestamp = g.start_timestamp.strftime('%Y%m%d%H%M%S')
        end_timestamp = g.end_timestamp.strftime('%Y%m%d%H%M%S')
        guide_elem = etree.SubElement(tv, "programme", channel=str(g.channel_id), start=start_timestamp, stop=end_timestamp)
        etree.SubElement(guide_elem, "title").text = escape(channel_name)
        if g.description:
            etree.SubElement(guide_elem, "desc").text = escape(g.description)
        for category in g.categories:
            etree.SubElement(guide_elem, "category").text = escape(category)

    xml = etree.tostring(tv, pretty_print=True, encoding="UTF-8", xml_declaration=False).decode("UTF-8")

    # Combine XML declaration, DOCTYPE, and XML content in the correct order
    declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    doctype = '<!DOCTYPE tv SYSTEM "xmltv.dtd">'
    return f'{declaration}\n{doctype}\n{xml}'


def build_playlist_proxy():
    pass