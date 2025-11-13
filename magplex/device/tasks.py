import random
import time
import zoneinfo
from datetime import datetime
import logging
from itertools import batched

from psycopg.errors import ForeignKeyViolation

from magplex.database.database import PostgresConnection
from magplex.device import database, parser
from magplex.utilities.localization import Locale


def save_channels(device_uid):
    from magplex.device.manager import DeviceManager
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        logging.warning(Locale.DEVICE_UNAVAILABLE(device_uid=device_uid))
        return None
    logging.info(Locale.TASK_RUNNING_CHANNEL_LIST_REFRESH(device_uid=user_device.device_uid))

    conn = PostgresConnection()
    log_uid = db_fk_safe(database.insert_device_task_log, conn, user_device.device_uid, 'save_channels')
    if log_uid is False:
        return None
    conn.commit()

    fetched_genres = user_device.get_genres()
    if fetched_genres is None:
        logging.warning(Locale.DEVICE_GENRE_LIST_UNAVAILABLE(device_uid=user_device.device_uid))
        return None

    for g in fetched_genres:
        g = parser.parse_genre(g)
        if g is None:
            continue
        success = db_fk_safe(database.insert_genre, conn, user_device.device_uid, g.genre_id, g.genre_number, g.genre_name)
        if success is False:
            return None
    conn.commit()

    genres = database.get_all_genres(conn, user_device.device_uid)
    fetched_channels = user_device.get_all_channels()
    if fetched_channels is None:
        logging.warning(Locale.DEVICE_CHANNEL_LIST_UNAVAILABLE(device_uid=user_device.device_uid))
        return None

    index = 0
    while index < len(fetched_channels):
        c = parser.parse_channel(fetched_channels[index], genres)
        if c is None:
            fetched_channels.pop(index)
            continue
        fetched_channels[index] = c
        success = db_fk_safe(database.insert_channel, conn, user_device.device_uid,c.channel_id, c.channel_number,
                                    c.channel_name, c.channel_hd, c.genre_id, c.stream_id)
        if success is False:
            return None
        index += 1
    conn.commit()

    # Mark missing channels as stale.
    existing_channels = database.get_channels(conn, user_device.device_uid)
    fetched_channel_ids = [c.channel_id for c in fetched_channels]
    for existing_channel in existing_channels:
        if existing_channel.channel_id not in fetched_channel_ids:
            database.update_channel(conn, user_device.device_uid, existing_channel.channel_id, channel_stale=True)
    conn.commit()

    # Get the latest copy of the channel list.
    channel_list = database.get_channels(conn, user_device.device_uid)
    database.update_device_task_log(conn, log_uid, datetime.now())
    logging.info(Locale.DEVICE_CHANNEL_LIST_SUCCESSFUL(device_uid=user_device.device_uid))
    conn.commit()
    conn.close()
    return channel_list


def save_channel_guides(device_uid):
    """Background task ran at an interval to populate the cache with EPG information."""
    from magplex.device.manager import DeviceManager
    user_device = DeviceManager.get_user_device(device_uid)
    if user_device is None:
        logging.error(Locale.DEVICE_UNAVAILABLE(device_uid=device_uid))
        return None
    logging.info(Locale.TASK_RUNNING_CHANNEL_GUIDE_REFRESH(device_uid=user_device.device_uid))

    conn = PostgresConnection()
    log_uid = db_fk_safe(database.insert_device_task_log, conn, user_device.device_uid, 'save_channel_guides')
    if log_uid is False:
        return None
    conn.commit()

    channel_list = database.get_channels(conn, user_device.device_uid, channel_enabled=True)
    if channel_list is None:
        logging.error(Locale.DEVICE_CHANNEL_LIST_UNAVAILABLE(device_uid=user_device.device_uid))
        return None
    conn.close()

    # Build a list of EPG links to get the program guide for each channel.
    device_profile = user_device.get_device_profile()
    guide_urls = []
    for channel in channel_list:
        link = f'http://{device_profile.portal}/stalker_portal/server/load.php?type=itv&action=get_short_epg&ch_id={channel.channel_id}&JsHttpRequest=1-xml'
        guide_urls.append(link)

    # Process the channel guide URLs in batches to prevent rate limiting.
    for link_batch in batched(guide_urls, 5):
        guide_batch = user_device.get_batch(link_batch)
        conn = PostgresConnection()
        for guides in guide_batch:
            if not guides or not isinstance(guides, list):
                continue

            for g in guides:
                g = parser.parse_channel_guide(g, device_profile.timezone)
                if g is None:
                    continue
                success = db_fk_safe(database.insert_channel_guide, conn, user_device.device_uid, g.channel_id,
                                     g.title, g.categories, g.description, g.start_timestamp, g.end_timestamp)
                if success is False:
                    return None
        conn.commit()
        conn.close()
        time.sleep(random.uniform(0, 3))

    conn = PostgresConnection()
    database.update_device_task_log(conn, log_uid, datetime.now(zoneinfo.ZoneInfo("Etc/UTC")))
    conn.commit()
    conn.close()
    return None


def db_fk_safe(fn, conn, device_uid, *args, **kwargs):
    """Calls a device database function safely. Returns the function value or True on success,
     and False on foreign key violation. Ensures the device wasn't deleted while a task is running."""
    try:
        result = fn(conn, device_uid, *args, **kwargs)
        if isinstance(result, bool):
            raise Exception("Cannot call foreign key safe on a database function returning a boolean.")
        return result if result else True
    except ForeignKeyViolation:
        logging.warning(Locale.DEVICE_NON_EXISTENT_ERROR(device_uid=device_uid))
        conn.close()
        return False