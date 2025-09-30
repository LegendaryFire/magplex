import sys
from datetime import datetime, timezone
import json
from concurrent.futures import ThreadPoolExecutor
import requests
import requests.adapters
from dataclasses import dataclass
import logging

import logs


@dataclass
class STBProfile:
    portal: str
    mac_address: str
    stb_lang: str
    timezone: str
    device_id: str
    device_id2: str
    signature: str


@dataclass
class STBGenre:
    id: int
    name: str


@dataclass
class STBChannel:
    number: int
    channel_id: int
    stream_id: int
    name: str
    genre: STBGenre


@dataclass
class STBGuideEntry:
    channel_id: int
    name: str
    description: str
    categories: list
    start: str
    end: str


class ErrorCodes:
    class InvalidChannelURLError(Exception):
        def __init__(self, message="Unable to generate a channel URL"):
            super().__init__(message)

    class InvalidResponseError(Exception):
        def __init__(self, message="Invalid response data was received"):
            super().__init__(message)

    class AuthTokenError(Exception):
        def __init__(self, message="Unable to receive authentication token"):
            super().__init__(message)


def build_config(profile: STBProfile):
    config = {'Headers': {
        'User-Agent': 'Mozilla/5.0 (Unknown; Linux) AppleWebKit/538.1 (KHTML, like Gecko) MAG200 stbapp ver: 4 rev: 734 Mobile Safari/538.1',
        'Referrer': f'http://{profile.portal}/stalker_portal/c/',
        'Accept-Language': f'{profile.stb_lang},*',
        'Host': f'{profile.portal}',
    }, 'Cookies': {
        'mac': f'{profile.mac_address}',
        'stb_lang': f'{profile.stb_lang}',
        'timezone': f'{profile.timezone}',
    }, 'Service': {
        'Token': f'http://{profile.portal}/stalker_portal/server/load.php?type=stb&action=handshake&token=&JsHttpRequest=1-xml',
        'Auth': f'http://{profile.portal}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=3&ver=ImageDescription:%202.20.04-420;%20ImageDate:%20Wed%20Aug%2019%2011:43:17%20UTC%202020;%20PORTAL%20version:%205.1.1;%20API%20Version:%20JS%20API%20version:%20348&num_banks=1&sn=092020N014162&stb_type=MAG420&image_version=220&video_out=hdmi&device_id={profile.device_id}&device_id2={profile.device_id2}&signature={profile.signature}&auth_second_step=0&hw_version=04D-P0L-00&not_valid_token=0&JsHttpRequest=1-xml',
        'Channel_List': f'http://{profile.portal}/stalker_portal/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml',
        'Create_URL': f'http://{profile.portal}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%20http://localhost/ch/stream_id&series=&forced_storage=undefined&disable_ad=0&download=0&JsHttpRequest=1-xml',
        'Genres': f'http://{profile.portal}/stalker_portal/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml',
        'Channel_Guide': f'http://{profile.portal}/stalker_portal/server/load.php?type=itv&action=get_short_epg&ch_id=channel_id&JsHttpRequest=1-xml',
    }}
    return config


class STB:
    def __init__(self, profile: STBProfile):
        self._session = requests.session()
        self._session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, pool_block=True))
        self._config = build_config(profile)
        self._authorize()
        self.__denied = False

    def _get(self, url):
        headers = self._config.get('Headers')
        cookies = self._config.get('Cookies')
        response = self._session.get(url, headers=headers, cookies=cookies)
        if 'Authorization failed' in response.text:
            if self.__denied:
                logging.warning("Portal authorization failed twice. Exiting now.")
                sys.exit()
            self.__denied = True
            logging.warning("Portal authorization failed, re-authenticating and trying again.")
            self._authorize()
            logging.info("Portal authentication successful!")
            self.__denied = False
            response = self._session.get(url, headers=headers, cookies=cookies)
        if response.status_code == 403:
            logging.error("Portal responded with status code 403. Exiting now.")
            sys.exit()
        self.__denied = False

        try:
            data = json.loads(response.text).get('js', None)
        except json.JSONDecodeError:
            helper.dump_error(response.text)
            raise ErrorCodes.InvalidResponseError("Unable to decode data. Data dumped to file.")

        if not isinstance(data, list) and not data:
            raise ErrorCodes.InvalidResponseError()
        return data

    def _get_list(self, urls, batch_size=2500):
        def fetch_url(url):
            try:
                response = self._get(url)
                return response
            except (ErrorCodes.InvalidResponseError, requests.exceptions.RequestException) as e:
                logging.warning(f"Error fetching {url}: {e}")
                return None

        def process_batch(batch_urls):
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                results = list(executor.map(fetch_url, batch_urls))
            filtered_results = [result for result in results if result is not None]
            return filtered_results

        def run_batch():
            results = []
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i + batch_size]
                batch_results = process_batch(batch_urls)
                results.extend(batch_results)
            return results

        return run_batch()

    def _authorize(self):
        """Authorizes the STB using device_id, device_id2 and signature."""
        token_url = self._config.get('Service', {}).get('Token')
        response = self._get(token_url)
        token = response.get('token', None)
        if not token:
            raise ErrorCodes.AuthTokenError()
        self._config['Headers']['Authorization'] = f'Bearer {token}'

        auth_url = self._config.get('Service', {}).get("Auth")
        self._get(auth_url)

    def get_genres(self):
        """Returns a list of STBGenre objects."""
        genre_url = self._config.get('Service', {}).get('Genres')
        response = self._get(genre_url)
        return [STBGenre(id=genre.get('id'), name=genre.get('title')) for genre in response]

    def get_channel_list(self):
        """Returns a list of STBChannel objects."""
        logging.info("Getting channel list.")
        channel_url = self._config.get('Service', {}).get('Channel_List')
        channel_data = self._get(channel_url).get('data')
        genre_data = {genre.id: genre for genre in self.get_genres()}
        results = []
        for channel in channel_data:
            channel_id = channel.get('id')
            number = channel.get('number')
            name = channel.get('name')
            genre = genre_data.get(channel.get('tv_genre_id'))
            stream_id = channel.get('cmds')
            if stream_id and isinstance(stream_id, list) and isinstance(stream_id[0], dict):
                stream_id = stream_id[0].get('id')
            else:
                stream_id = None
            if all([channel_id, number, name, genre, stream_id]):
                stb_channel = STBChannel(channel_id=channel_id, stream_id=stream_id, number=number, name=name, genre=genre)
                results.append(stb_channel)
        return results

    def get_channel_guide(self) -> list[STBGuideEntry]:
        """Returns a list of STBGuideEntry objects for each channel."""
        guide_url = self._config.get('Service', {}).get('Channel_Guide')
        channel_list = self.get_channel_list()
        url_list = [guide_url.replace('channel_id', str(channel.channel_id)) for channel in channel_list]
        results = self._get_list(url_list)

        guide_data = []
        for channel_epg in results:
            if not isinstance(channel_epg, list) or not list:
                continue
            for entry_data in channel_epg:
                epg_entry = _build_guide_entry(entry_data)
                if epg_entry:
                    guide_data.append(epg_entry)
        return guide_data

    def get_channel_url(self, channel_id):
        """Generates a channel URL from channel ID."""
        create_url = self._config.get('Service', {}).get('Create_URL')
        create_url = create_url.replace('stream_id', str(channel_id))
        response = self._get(create_url)
        generated_url = response.get('cmd')
        if not generated_url:
            raise ErrorCodes.InvalidChannelURLError()
        return generated_url


def _build_guide_entry(guide_data):
    """Builds a STBGuideEntry object from dictionary data. Returns None if passed invalid data."""
    channel_id = guide_data.get('ch_id')
    name, description = guide_data.get('name'), guide_data.get('descr')
    start, end = guide_data.get('start_timestamp'), guide_data.get('stop_timestamp')
    categories = [category.strip() for category in guide_data.get('category', str()).split(',') if category.strip()]
    if all([channel_id, name, str(start).isdigit(), str(end).isdigit()]):
        start = datetime.fromtimestamp(int(start), tz=timezone.utc).strftime('%Y%m%d%H%M%S')
        end = datetime.fromtimestamp(int(end), tz=timezone.utc).strftime('%Y%m%d%H%M%S')
        guide = STBGuideEntry(channel_id=channel_id, name=name, description=description,
                              categories=categories, start=start, end=end)
    else:
        return None
    return guide
