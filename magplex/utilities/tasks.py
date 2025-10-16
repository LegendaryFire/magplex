import logging
import time

from magplex.utilities import cache


def set_device_channel_guide():
    """Background task ran at an interval to populate the cache with EPG information."""
    from magplex.utilities.device import DeviceManager
    device = DeviceManager.get_device()
    if device is None:
        logging.error(f"Unable to get device. Please check configuration.")
        return
    logging.info(f"Setting channel guide for device {device.id}.")
    channel_list = device.get_channel_list()
    if channel_list is None:
        logging.error('Failed to update channel guide. Channel list is None.')
        return

    # Build a list of EPG links to get the program guide for each channel.
    guide_urls = []
    logging.info("Getting channel list to build EPG links.")
    for channel in channel_list:
        channel_id = channel.get('channel_id')
        guide_url = f'http://{device.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_short_epg&ch_id={channel_id}&JsHttpRequest=1-xml'
        guide_urls.append(guide_url)
        cache.insert_channel_id(device.cache_conn, device.id, channel_id)
        cache.insert_channel(device.cache_conn, device.id, channel_id, channel)

    # Process the channel guide URLs in batches to prevent rate limiting.
    guide_count = len(guide_urls)
    while len(guide_urls) > 0:
        logging.info(f"Fetching EPG, {guide_count - len(guide_urls)} of {guide_count}.")
        current_batch = guide_urls[:3]
        guide_urls = guide_urls[3:]
        responses = device.get_list(current_batch)
        for channel_guides in responses:
            if not channel_guides or not isinstance(channel_guides, list):
                continue

            channel_id = channel_guides[0].get('ch_id')
            for index, channel_guide in enumerate(channel_guides):
                start_timestamp =  channel_guide.get('start_timestamp')
                stop_timestamp = channel_guide.get('stop_timestamp')
                if not start_timestamp or not stop_timestamp:
                    continue

                channel_guides[index] = {
                    'channel_id': channel_id,
                    'channel_name': channel_guide.get('name'),
                    'channel_description': channel_guide.get('descr'),
                    'start_timestamp': int(start_timestamp),
                    'stop_timestamp': int(stop_timestamp),
                    'categories': [c.strip() for c in channel_guide.get('category', str()).split(',') if c.strip()]
                }

            cache.insert_channel_guide(device.cache_conn, device.id, channel_id, channel_guides)
        time.sleep(0.25)  # 250ms delay to prevent rate limiting.
