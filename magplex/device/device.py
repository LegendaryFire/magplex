import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http import HTTPStatus

import requests
from apscheduler.jobstores.base import ConflictingIdError
from requests.adapters import HTTPAdapter

from magplex.device import cache, tasks
from magplex import users
from magplex.device.localization import ErrorMessage
from magplex.utilities.database import RedisPool, LazyPostgresConnection
from magplex.utilities.scheduler import TaskManager


class DeviceManager:
    _device = None

    @classmethod
    def create_device(cls):
        conn = LazyPostgresConnection()
        device_profile = users.database.get_user_device(conn)
        if device_profile is None:
            return None
        conn.close()
        return Device(device_profile)

    @classmethod
    def get_device(cls):
        if cls._device is None:
            cls._device = cls.create_device()
        return cls._device

    @classmethod
    def reset_device(cls):
        cls._device = None


class Device:
    def __init__(self, profile):
        self.device_uid = str(profile.device_uid)
        self.authorized = True
        self.adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.session = requests.session()
        self.session.mount("http://", self.adapter)
        self.session.mount("https://", self.adapter)
        self.profile = profile
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Unknown; Linux) AppleWebKit/538.1 (KHTML, like Gecko) MAG200 stbapp ver: 4 rev: 734 Mobile Safari/538.1',
            'Accept-Language': f'{profile.language},*',
            'Host': f'{profile.portal}',
            'Referrer': f'http://{profile.portal}/stalker_portal/c/',
        }
        self.cookies = {
            'mac': f'{profile.mac_address.replace('-', ':')}',
            'stb_lang': f'{profile.language}',
            'timezone': f'{profile.timezone}',
        }
        self._schedule_tasks()


    def _schedule_tasks(self):
        job_interval_map = {tasks.save_channels: 1, tasks.save_device_channel_guide: 1}
        scheduler = TaskManager.get_scheduler()
        for job, hours in job_interval_map.items():
            job_name = f'{self.device_uid}:{job.__name__}'
            try:
                if scheduler.get_job(job_name) is not None:
                    logging.warning('Scheduler background task already exists, skipping.')
                    continue
                scheduler.add_job(job, 'interval', hours=hours, id=job_name, next_run_time=datetime.now(timezone.utc))
            except ConflictingIdError:
                logging.warning('Scheduler conflicting ID error ignored')


    def _awaiting_timeout(self):
        cache_conn = RedisPool.get_connection()
        awaiting_timeout = cache.get_device_timeout(cache_conn, self.device_uid)
        if awaiting_timeout:
            logging.warning(ErrorMessage.DEVICE_AWAITING_TIMEOUT)

        return awaiting_timeout


    def __validate_response_text(self, response):
        invalid_responses = {'Authorization failed', 'Access denied'}
        valid_response = True
        if response.status_code != HTTPStatus.OK:
            logging.warning('Invalid response code received')
            valid_response = False
        for response_text in invalid_responses:
            if response_text in response.text:
                logging.warning('Invalid text found in response')
                valid_response = False
        if not valid_response:
            self.headers.pop('Authorization', None)

        return valid_response


    def __validate_response_json(self, response):
        try:
            data = json.loads(response.text)
            if data is None or not isinstance(data, (list, dict)):
                logging.warning(ErrorMessage.DEVICE_RESPONSE_UNEXPECTED_JSON)
                return False
        except json.JSONDecodeError:
            logging.warning(ErrorMessage.DEVICE_RESPONSE_NOT_JSON)
            return False

        return True


    def refresh_access_token(self):
        """Gets the authentication token for the session."""
        awaiting_timeout = self._awaiting_timeout()
        if awaiting_timeout:
            return None

        self.headers.pop('Authorization', None)  # Remove the old authentication header.
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=stb&action=handshake&token=&JsHttpRequest=1-xml'
        response = self.session.get(url, headers=self.headers, cookies=self.cookies, timeout=15)

        # Check for a valid response.
        valid_response = self.__validate_response_text(response)
        if not valid_response:
            logging.warning(ErrorMessage.DEVICE_INVALID_RESPONSE_TEXT)
            return None

        try:
            response_data = json.loads(response.text).get('js', {})
            access_token = response_data.get('token')
            random_token = response_data.get('random')
        except json.JSONDecodeError:
            return None

        if not access_token:
            return None

        cache_conn = RedisPool.get_connection()
        cache.set_access_token(cache_conn, self.device_uid, access_token)
        cache.set_access_random(cache_conn, self.device_uid, random_token)
        self.headers['Authorization'] = f'Bearer {access_token}'
        if random_token is not None:
            self.headers['X-Random'] = random_token
            self.headers['Random'] = random_token

        return access_token


    def refresh_authorization(self):
        pass


    def update_access_token(self):
        cache_conn = RedisPool.get_connection()
        access_token = cache.get_access_token(cache_conn, self.device_uid)
        if access_token is not None:
            self.headers.update({'Authorization': f'Bearer {access_token}'})
        random_token = cache.get_access_random(cache_conn, self.device_uid)
        if random_token is not None:
            self.headers.update({'X-Random': f'{random_token}'})
            self.headers.update({'Random': f'{random_token}'})


    def is_authorized(self):
        return 'Authorization' in self.headers


    def invalidate_authorization(self):
        cache_conn = RedisPool.get_connection()
        cache.expire_access(cache_conn, self.device_uid)
        self.headers.pop('Authorization', None)
        self.headers.pop('X-Random', None)
        self.headers.pop('Random', None)


    def update_authorization(self):
        """Gets authentication for the set-top box device."""
        awaiting_timeout = self._awaiting_timeout()
        if awaiting_timeout:
            return None

        self.update_access_token()
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=stb&action=get_profile&hd=3&ver=ImageDescription:%202.20.04-420;%20ImageDate:%20Wed%20Aug%2019%2011:43:17%20UTC%202020;%20PORTAL%20version:%205.1.1;%20API%20Version:%20JS%20API%20version:%20348&num_banks=1&sn=092020N014162&stb_type=MAG420&image_version=220&video_out=hdmi&device_id={self.profile.device_id1}&device_id2={self.profile.device_id2}&signature={self.profile.signature}&auth_second_step=0&hw_version=04D-P0L-00&not_valid_token=0&JsHttpRequest=1-xml'
        response = self.session.get(url, headers=self.headers, cookies=self.cookies, timeout=15)
        valid_response = self.__validate_response_text(response)
        if not valid_response:
            return None

        valid_json = self.__validate_response_json(response)
        if not valid_json:
            return None

        return json.loads(response.text).get('js', None)


    def get(self, url):
        """Authenticated get method for portal endpoints."""
        awaiting_timeout = self._awaiting_timeout()
        if awaiting_timeout:
            return None

        self.update_access_token()
        response = self.session.get(url, headers=self.headers, cookies=self.cookies, timeout=15)

        # An invalid authorization will still return a 200 status code. Check the payload and reauthenticate.
        valid_response = self.__validate_response_text(response)
        if not valid_response:
            cache_conn = RedisPool.get_connection()
            # Attempt to refresh the access token.
            access_token = self.refresh_access_token()
            if access_token is None:
                logging.warning(ErrorMessage.DEVICE_ACCESS_TOKEN_UNAVAILABLE)
                cache.set_device_timeout(cache_conn, self.device_uid)
                self.invalidate_authorization()
                return None

            is_authorized = self.update_authorization()
            if is_authorized is None:
                logging.warning(ErrorMessage.DEVICE_AUTHORIZATION_FAILED)
                cache.set_device_timeout(cache_conn, self.device_uid)
                self.invalidate_authorization()
                return None

            # Recursively retry the get command.
            return self.get(url)

        valid_json = self.__validate_response_json(response)
        if not valid_json:
            return None

        return json.loads(response.text).get('js', None)


    def get_batch(self, urls):
        def get(url):
            try:
                get_response = self.get(url)
                return get_response
            except requests.exceptions.RequestException:
                return None

        with ThreadPoolExecutor(max_workers=3) as executor:
            response_list = list(executor.map(get, urls))

        # Filter out failed responses.
        filtered_responses = []
        for response in response_list:
            if response:
                filtered_responses.append(response)

        return filtered_responses


    def get_channel_playlist(self, stream_id):
        """Gets a generated channel playlist URL from stream ID."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%20http://localhost/ch/{stream_id}&series=&forced_storage=undefined&disable_ad=0&download=0&JsHttpRequest=1-xml'
        data = self.get(url)
        if data is None:
            logging.warning("Unable to retrieve channel playlist.")
            return None

        # Attempt to get the stream ID from the channel playlist command.
        stream_link = data.get('cmd')
        if not stream_link:
            error = data.get('error')
            if error == 'link_fault':
                logging.warning(f"Unable to get playlist link. Stream ID {stream_id} does not exist.")
                return None
            else:
                logging.warning("Unable to get playlist link. Unknown error.")
                return None

        return stream_link


    def get_genres(self):
        """Gets a list of genres from the portal."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml'
        genre_list = self.get(url)
        if genre_list is None:
            logging.warning("Unable to retrieve genres.")
            return None

        return genre_list


    def get_all_channels(self):
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml'
        data = self.get(url)
        if data is None:
            logging.warning('Unable to get channel list.')
            return None

        channels = data.get('data') if data else None
        return channels
