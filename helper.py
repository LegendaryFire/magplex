from xml.sax.saxutils import escape
from jinja2 import Template
from lxml import etree


def build_playlist(channels, domain):
    template_data = """
        #EXTM3U
        #EXT-X-VERSION:3
        {% for channel in channels %}
            #EXTINF:-1 tvg-id="{{channel.channel_id}}" tvg-name="{{channel.name}}" group-title="{{channel.genre.name}}",{{channel.name}}
            {{ domain }}/channel/{{ channel.stream_id }}
        {% endfor %}
    """
    template_data = '\n'.join(line.strip() for line in template_data.splitlines() if line.strip())
    template = Template(template_data)
    return template.render(channels=channels, domain=domain)


def build_channel_guide(channels, guides):
    tv = etree.Element(
        "tv",
        attrib={
            "generator-info-name": "XMLTV",
            "source-info-name": "MagPlex by Tristan Balon",
        }
    )
    for channel in channels:
        channel_elem = etree.SubElement(tv, "channel", id=channel.channel_id)
        etree.SubElement(channel_elem, "display-name").text = escape(channel.name)

    for guide in guides:
        guide_elem = etree.SubElement(tv, "programme", channel=guide.channel_id, start=guide.start, stop=guide.end)
        etree.SubElement(guide_elem, "title").text = escape(guide.name)
        if guide.description:
            etree.SubElement(guide_elem, "desc").text = escape(guide.description)
        for category in guide.categories:
            etree.SubElement(guide_elem, "category").text = escape(category)

    xml_str = etree.tostring(tv, pretty_print=True, encoding="UTF-8", xml_declaration=False).decode("UTF-8")
    # Combine XML declaration, DOCTYPE, and XML content in the correct order
    doctype = '<!DOCTYPE tv SYSTEM "xmltv.dtd">'
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    channel_guide = f'{xml_declaration}\n{doctype}\n{xml_str}'
    return channel_guide
