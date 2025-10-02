import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from apscheduler.schedulers.background import BackgroundScheduler

import requests
from flask import Response

from utilities import cache

scheduler = BackgroundScheduler()
scheduler.start()

@dataclass
class Profile:
    portal: str
    mac: str
    timezone: str
    language: str
    device_id: str
    device_id2: str
    signature: str


class Device:
    def __init__(self, conn, profile):
        self.conn = conn
        self.id = profile.mac
        self.authorized = True
        self.session = requests.session()
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, pool_block=True))
        self.profile = profile
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Unknown; Linux) AppleWebKit/538.1 (KHTML, like Gecko) MAG200 stbapp ver: 4 rev: 734 Mobile Safari/538.1',
            'Accept-Language': f'{profile.language},*',
            'Host': f'{profile.portal}',
            'Referrer': f'http://{profile.portal}/stalker_portal/c/',
        }
        self.cookies = {
            'mac': f'{profile.mac}',
            'stb_lang': f'{profile.language}',
            'timezone': f'{profile.timezone}',
        }
        scheduler.add_job(self._get_channel_guide, 'interval', minutes=5, id=self.id, next_run_time=datetime.now())

    def __del__(self):
        scheduler.remove_job(self.id)

    def get_token(self):
        """Gets the authentication token for the session."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=stb&action=handshake&token=&JsHttpRequest=1-xml'
        self.headers.pop('Authorization', None)  # Remove the old authentication header.
        response = self.session.get(url, headers=self.headers, cookies=self.cookies)

        # Check for a valid response.
        if response.status_code != HTTPStatus.OK or 'Authorization failed' in response.text:
            return None

        # Attempt to deserialize the response and return the token if it exists.
        try:
            token = json.loads(response.text).get('js', {}).get('token')
            return token if token else None
        except json.JSONDecodeError:
            return None

    def get_authorization(self):
        """Gets authentication for the set-top box device."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=3&ver=ImageDescription:%202.20.04-420;%20ImageDate:%20Wed%20Aug%2019%2011:43:17%20UTC%202020;%20PORTAL%20version:%205.1.1;%20API%20Version:%20JS%20API%20version:%20348&num_banks=1&sn=092020N014162&stb_type=MAG420&image_version=220&video_out=hdmi&device_id={self.profile.device_id}&device_id2={self.profile.device_id2}&signature={self.profile.signature}&auth_second_step=0&hw_version=04D-P0L-00&not_valid_token=0&JsHttpRequest=1-xml'
        response = self.session.get(url, headers=self.headers, cookies=self.cookies)
        if response.status_code != HTTPStatus.OK or 'Authorization failed' in response.text:
            self.headers.pop('Authorization', None)  # Clear the authentication header on failure.
            return False
        return True

    def get(self, url):
        """Authenticated get method for portal endpoints."""
        response = self.session.get(url, headers=self.headers, cookies=self.cookies)

        # An invalid authorization will still return a 200 status code. Check the payload and reauthenticate.
        if not self.authorized or response.status_code == HTTPStatus.FORBIDDEN or 'Authorization failed' in response.text:
            token = self.get_token()
            if token is not None:
                self.headers['Authorization'] = f'Bearer {token}'  # Set authorization header on success.
                authorized = self.get_authorization()
                if not authorized:
                    logging.warning("Unable to authorize.")
                    self.authorized = False
                    return None
                return self.get(url)
            else:
                logging.warning('Unable to retrieve token.')
                self.authorized = False
                return None

        self.authorized = True

        try:
            data = json.loads(response.text).get('js', None)
            # We always expect either a list or a dictionary from the endpoints.
            if data is None or not isinstance(data, (list, dict)):
                logging.warning(f"Unknown response data received. Status code {response.status_code}.")
                return None
        except json.JSONDecodeError:
            self.authorized = False
            logging.warning("Unable to decode response data.")
            return None

        return data

    def get_list(self, urls):
        def fetch_url(url):
            try:
                response = self.get(url)
                return response
            except requests.exceptions.RequestException:
                return None

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(fetch_url, urls))

        # Filter out failed responses.
        return [result for result in results if result is not None]

    def get_channel(self, stream_id):
        """Gets a generated channel URL from stream ID."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%20http://localhost/ch/{stream_id}&series=&forced_storage=undefined&disable_ad=0&download=0&JsHttpRequest=1-xml'
        data = self.get(url)
        if data is None or not isinstance(data, dict):
            logging.warning("Unable to retrieve channel.")
            return None
        return data.get('cmd')

    def get_genres(self):
        """Gets a list of genres from the portal."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml'
        genre_list = self.get(url)
        if genre_list is None or not isinstance(genre_list, list):
            logging.warning("Unable to retrieve genres.")
            return None

        # Iterate in reverse to make sure pop doesn't affect the enumeration.
        for index in reversed(range(len(genre_list))):
            genre = genre_list[index]
            genre_list[index] = {
                'genre_id': genre.get('id'),
                'genre_number': genre.get('number'),
                'genre_name': genre.get('title')
            }

            # Skip the genre if invalid data was found.
            if any(v is None for v in genre_list[index].values()):
                genre_list.pop(index)
                continue

        return genre_list

    def get_channel_list(self):
        """Gets a list of available channels from the portal."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml'
        data = self.get(url)
        if data is None:
            return Response("Unable to get channel list.", HTTPStatus.INTERNAL_SERVER_ERROR)

        channel_list = data.get('data') if data else None
        if not channel_list or not isinstance(channel_list, list):
            return None

        # Iterate in reverse to make sure pop doesn't affect the enumeration.
        for index in reversed(range(len(channel_list))):
            channel = channel_list[index]
            streams = channel.get('cmds')
            stream_id = streams[0].get('id') if streams and isinstance(streams[0], dict) else None
            channel_list[index] = {
                'channel_name': channel.get('name'),
                'channel_id': channel.get('id'),
                'channel_number': channel.get('number'),
                'genre_id': channel.get('tv_genre_id'),
                'stream_id': stream_id
            }

            # Skip the channel if invalid data was found.
            if any(v is None for v in channel_list[index].values()):
                channel_list.pop(index)
                continue

        return channel_list

    def get_channel_guide(self):
        """Gets the channel guide from available EPG data stored in the cache server."""
        return {
            'channels': cache.get_all_channels(self.conn, self.id),
            'channel_guides': cache.get_all_channel_guides(self.conn, self.id),
        }

    def _get_channel_guide(self):
        """Background task ran at an interval to populate the cache with EPG information."""
        channel_list = self.get_channel_list()

        # Build a list of EPG links to get the program guide for each channel.
        guide_urls = []
        for channel in channel_list:
            channel_id = channel.get('channel_id')
            guide_url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_short_epg&ch_id={channel_id}&JsHttpRequest=1-xml'
            guide_urls.append(guide_url)
            cache.insert_channel_id(self.conn, self.id, channel_id)
            cache.insert_channel(self.conn, self.id, channel_id, channel)

        # Process the channel guide URLs in batches to prevent rate limiting.
        while len(guide_urls) > 0:
            current_batch = guide_urls[:50]
            guide_urls = guide_urls[50:]
            responses = self.get_list(current_batch)
            for channel_guides in responses:
                if not channel_guides or not isinstance(channel_guides, list):
                    continue

                channel_id = channel_guides[0].get('ch_id')
                for index, channel_guide in enumerate(channel_guides):
                    channel_guides[index] = {
                        'channel_id': channel_id,
                        'channel_name': channel_guide.get('name'),
                        'channel_description': channel_guide.get('descr'),
                        'start_timestamp': int(channel_guide.get('start_timestamp')),
                        'stop_timestamp': int(channel_guide.get('stop_timestamp')),
                        'categories': [c.strip() for c in channel_guide.get('category', str()).split(',') if c.strip()]
                    }

                cache.insert_channel_guide(self.conn, self.id, channel_id, channel_guides)
            time.sleep(0.15)  # 150ms delay to prevent rate limiting.