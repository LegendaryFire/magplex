import logging
from datetime import datetime
from itertools import batched

from magplex.device.localization import ErrorMessage
from magplex.utilities.database import LazyPostgresConnection
from magplex.device import database, parser


def save_channels():
    from magplex.device.device import DeviceManager
    device = DeviceManager.get_device()
    if device is None:
        logging.warning(ErrorMessage.DEVICE_UNAVAILABLE)
        return None

    fetched_channels = device.get_all_channels()
    if fetched_channels is None:
        logging.warning(ErrorMessage.DEVICE_CHANNEL_LIST_UNAVAILABLE)
        return None

    conn = LazyPostgresConnection()
    index = 0
    while index < len(fetched_channels):
        c = parser.parse_channel(fetched_channels[index])
        if c is None:
            fetched_channels.pop(index)
            continue
        database.insert_channel(conn, device.device_uid, c.channel_id, c.channel_number,
                                c.channel_name, c.channel_hd, c.genre_number, c.stream_id)
        index += 1
    conn.commit()

    # Mark missing channels as stale.
    existing_channels = database.get_all_channels(conn, device.device_uid)
    fetched_channel_ids = [c.channel_id for c in fetched_channels]
    for existing_channel in existing_channels:
        if existing_channel.channel_id not in fetched_channel_ids:
            database.update_channel_stale(conn, device.device_uid, existing_channel.channel_id, True)
    conn.commit()

    # Get the latest copy of the channel list.
    channel_list = database.get_all_channels(conn, device.device_uid)
    logging.warning(ErrorMessage.DEVICE_CHANNEL_LIST_SUCCESSFUL)
    conn.close()
    return channel_list


def save_device_channel_guide():
    """Background task ran at an interval to populate the cache with EPG information."""
    from magplex.device.device import DeviceManager
    user_device = DeviceManager.get_device()
    if user_device is None:
        logging.error(ErrorMessage.DEVICE_UNAVAILABLE)
        return
    logging.info(f"Setting channel guide for device {user_device.device_uid}.")

    db_conn = LazyPostgresConnection()
    channel_list = database.get_enabled_channels(db_conn, user_device.device_uid)
    if channel_list is None:
        logging.error('Failed to update channel guide. Channel list is None.')
        return
    db_conn.close()

    # Build a list of EPG links to get the program guide for each channel.
    guide_urls = []
    for channel in channel_list:
        link = f'http://{user_device.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_short_epg&ch_id={channel.channel_id}&JsHttpRequest=1-xml'
        guide_urls.append(link)

    # Process the channel guide URLs in batches to prevent rate limiting.
    logging.info(f"Fetching channel guide data for device {user_device.device_uid}.")
    for link_batch in batched(guide_urls, 3):
        responses = user_device.get_batch(link_batch)
        conn = LazyPostgresConnection()
        for response in responses:
            if not response or not isinstance(response, list):
                continue

            for channel_guide in response:
                channel_id = channel_guide.get('ch_id')
                start_timestamp = datetime.fromtimestamp(channel_guide.get('start_timestamp'))
                stop_timestamp = datetime.fromtimestamp(channel_guide.get('stop_timestamp'))
                title = channel_guide.get('name')
                description = channel_guide.get('descr')
                categories = [c.strip() for c in channel_guide.get('category', str()).split(',') if c.strip()]
                if not start_timestamp or not stop_timestamp:
                    continue
                database.insert_channel_guide(conn, user_device.device_uid, channel_id, title, categories, description,
                                              start_timestamp, stop_timestamp)
        conn.commit()
        conn.close()
