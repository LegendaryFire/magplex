import logging

from magplex.utilities.database import LazyPostgresConnection
import magplex.database.channels as db_channels

def set_channels():
    from magplex.device.device import DeviceManager
    device = DeviceManager.get_device()
    if device is None:
        logging.warning(f"Unable to get device. Please check configuration.")
        return None
    logging.info(f"Setting channel guide for device {device.id}.")
    url = f'http://{device.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml'
    data = device.get(url)
    if data is None:
        logging.warning('Unable to get channel list.')

    channel_list = data.get('data') if data else None
    if not channel_list or not isinstance(channel_list, list):
        return None

    conn = LazyPostgresConnection()
    inserted_channels = set()
    for channel in channel_list:
        channel_id = channel.get('id')
        channel_number = channel.get('number')
        channel_name = channel.get('name')
        channel_hd = channel.get('hd', '0') == '1'
        genre_number = channel.get('tv_genre_id')
        streams = channel.get('cmds')
        stream_id = streams[0].get('id') if streams and isinstance(streams[0], dict) else None
        fields = [channel_id, channel_number, channel_name, channel_hd, genre_number, stream_id]
        if any([field is None for field in fields]):
            logging.warning(f"Missing fields for channel {channel_id}.")
            continue
        db_channels.insert_channel(conn, device.device_uid, channel_id, channel_number, channel_name, channel_hd,
                                   genre_number, stream_id, channel_enabled=None)
        inserted_channels.add(channel_id)
    conn.commit()

    # Filter through the channels and make sure all of them exist. Remove the stale channels automatically.
    channel_list = db_channels.get_channels(conn, device.device_uid)
    for channel in channel_list:
        if channel.channel_id not in inserted_channels:
            db_channels.delete_channel(conn, device.device_uid, channel.channel_id)

    # Get the latest copy of the channel list.
    channel_list = db_channels.get_channels(conn, device.device_uid)
    logging.warning(f'Channel list background task completed successfully for device {device.id}.')
    conn.close()
    return channel_list

def set_device_channel_guide():
    """Background task ran at an interval to populate the cache with EPG information."""
    from magplex.device.device import DeviceManager
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
    logging.info(f"Fetching channel guide data for device {device.id}.")
    while len(guide_urls) > 0:
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
