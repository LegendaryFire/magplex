import logging
from itertools import batched

from magplex.database.database import PostgresConnection
from magplex.device import database, parser
from magplex.utilities.localization import Locale


def save_channels(device_uid):
    from magplex.device.manager import DeviceManager
    logging.info(Locale.TASK_RUNNING_CHANNEL_LIST_REFRESH)
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        logging.warning(Locale.DEVICE_UNAVAILABLE)
        return None

    fetched_genres = user_device.get_genres()
    if fetched_genres is None:
        logging.warning(Locale.DEVICE_GENRE_LIST_UNAVAILABLE)
        return None

    conn = PostgresConnection()
    for g in fetched_genres:
        g = parser.parse_genre(g)
        if g is None:
            continue
        database.insert_genre(conn, user_device.device_uid, g.genre_id, g.genre_number, g.genre_name)
    conn.commit()

    genres = database.get_all_genres(conn, user_device.device_uid)
    fetched_channels = user_device.get_all_channels()
    if fetched_channels is None:
        logging.warning(Locale.DEVICE_CHANNEL_LIST_UNAVAILABLE)
        return None

    index = 0
    while index < len(fetched_channels):
        c = parser.parse_channel(fetched_channels[index], genres)
        if c is None:
            fetched_channels.pop(index)
            continue
        fetched_channels[index] = c
        database.insert_channel(conn, user_device.device_uid, c.channel_id, c.channel_number,
                                c.channel_name, c.channel_hd, c.genre_id, c.stream_id)
        index += 1
    conn.commit()

    # Mark missing channels as stale.
    existing_channels = database.get_all_channels(conn, user_device.device_uid)
    fetched_channel_ids = [c.channel_id for c in fetched_channels]
    for existing_channel in existing_channels:
        if existing_channel.channel_id not in fetched_channel_ids:
            database.update_channel_stale(conn, user_device.device_uid, existing_channel.channel_id, True)
    conn.commit()

    # Get the latest copy of the channel list.
    channel_list = database.get_all_channels(conn, user_device.device_uid)
    logging.warning(Locale.DEVICE_CHANNEL_LIST_SUCCESSFUL)
    conn.close()
    return channel_list


def save_channel_guides(device_uid):
    """Background task ran at an interval to populate the cache with EPG information."""
    from magplex.device.manager import DeviceManager
    logging.info(Locale.TASK_RUNNING_CHANNEL_GUIDE_REFRESH)
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        logging.error(Locale.DEVICE_UNAVAILABLE)
        return

    conn = PostgresConnection()
    channel_list = database.get_enabled_channels(conn, user_device.device_uid)
    if channel_list is None:
        logging.error(Locale.DEVICE_CHANNEL_LIST_UNAVAILABLE)
        return
    conn.close()

    # Build a list of EPG links to get the program guide for each channel.
    guide_urls = []
    for channel in channel_list:
        link = f'http://{user_device.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_short_epg&ch_id={channel.channel_id}&JsHttpRequest=1-xml'
        guide_urls.append(link)

    # Process the channel guide URLs in batches to prevent rate limiting.
    for link_batch in batched(guide_urls, 3):
        guide_batch = user_device.get_batch(link_batch)
        conn = PostgresConnection()
        for guides in guide_batch:
            if not guides or not isinstance(guides, list):
                continue

            for g in guides:
                g = parser.parse_channel_guide(g, user_device.profile.timezone)
                if g is None:
                    continue
                database.insert_channel_guide(conn, user_device.device_uid, g.channel_id, g.title, g.categories,
                                              g.description, g.start_timestamp, g.end_timestamp)
        conn.commit()
        conn.close()
