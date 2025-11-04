import base64
import hashlib
import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http import HTTPStatus

import requests
from apscheduler.jobstores.base import ConflictingIdError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from requests.adapters import HTTPAdapter

from magplex import users
from magplex.database.database import PostgresConnection, RedisPool
from magplex.device import cache, tasks
from magplex.utilities.localization import Locale
from magplex.utilities.scheduler import TaskManager


class DeviceManager:
    _device = None

    @classmethod
    def create_device(cls):
        conn = PostgresConnection()
        device_profile = users.database.get_user_device_profile(conn)
        if device_profile is None:
            return None
        conn.close()
        return Device(device_profile)

    @classmethod
    def get_device(cls):
        if cls._device is None:
            cls._device = cls.create_device()
        return cls._device


class Device:
    def __init__(self, profile):
        self.device_uid = str(profile.device_uid)
        self.adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.session = requests.session()
        self.session.mount("http://", self.adapter)
        self.session.mount("https://", self.adapter)
        self.profile = profile
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Unknown; Linux) AppleWebKit/538.1 (KHTML, like Gecko) MAG200 stbapp ver: 4 rev: 734 Mobile Safari/538.1',
            'Accept-Language': f'en,*',
            'Host': f'{profile.portal}',
            'Referrer': f'http://{profile.portal}/stalker_portal/c/',
        }
        self.cookies = {
            'mac': f'{profile.mac_address.replace('-', ':')}',
            'stb_lang': f'en',
            'timezone': f'{profile.timezone}',
        }
        self._schedule_tasks()


    def _schedule_tasks(self):
        scheduler = TaskManager.get_scheduler()
        jobs = {
            tasks.save_channels: {'hours': 1, 'args': [self.device_uid]},
            tasks.save_channel_guides: {'hours': 1, 'args': [self.device_uid]}
        }

        for job, kwargs in jobs.items():
            job_name = f'{self.device_uid}:{job.__name__}'
            try:
                if scheduler.get_job(job_name) is not None:
                    continue
                scheduler.add_job(job, 'interval', id=job_name, next_run_time=datetime.now(timezone.utc), **kwargs)
                logging.info(Locale.TASK_JOB_ADDED_SUCCESSFULLY)
            except ConflictingIdError:
                logging.warning(Locale.TASK_CONFLICTING_JOB_IGNORED)


    def _awaiting_timeout(self):
        cache_conn = RedisPool.get_connection()
        awaiting_timeout = cache.get_device_timeout(cache_conn, self.device_uid)
        if awaiting_timeout:
            logging.warning(Locale.DEVICE_AWAITING_TIMEOUT)

        return awaiting_timeout


    def __validate_response_text(self, response):
        invalid_responses = {'Authorization failed', 'Access denied'}
        valid_response = True
        if response.status_code != HTTPStatus.OK:
            logging.warning(Locale.DEVICE_INVALID_RESPONSE_CODE)
            valid_response = False
        for response_text in invalid_responses:
            if response_text in response.text:
                logging.warning(Locale.DEVICE_INVALID_RESPONSE_TEXT)
                valid_response = False
        if not valid_response:
            self.headers.pop('Authorization', None)

        return valid_response


    def __validate_response_json(self, response):
        try:
            data = json.loads(response.text)
            if data is None or not isinstance(data, (list, dict)):
                logging.warning(Locale.DEVICE_RESPONSE_UNEXPECTED_JSON)
                return False
        except json.JSONDecodeError:
            logging.warning(Locale.DEVICE_RESPONSE_NOT_JSON)
            return False

        return True


    def get_device_encryption_key(self):
        """Gets the unique device hash, to be used as an encryption key."""
        return hashlib.sha256(uuid.UUID(self.device_uid).bytes).digest()


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
            logging.warning(Locale.DEVICE_INVALID_RESPONSE_TEXT)
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
        cache.set_device_access_token(cache_conn, self.device_uid, access_token)
        cache.set_device_access_random(cache_conn, self.device_uid, random_token)
        self.headers['Authorization'] = f'Bearer {access_token}'
        if random_token is not None:
            self.headers['X-Random'] = random_token
            self.headers['Random'] = random_token

        return access_token


    def update_access_token(self):
        """Fetch a new access token and update authorization headers."""
        cache_conn = RedisPool.get_connection()
        access_token = cache.get_device_access_token(cache_conn, self.device_uid)
        if access_token is not None:
            self.headers.update({'Authorization': f'Bearer {access_token}'})
        random_token = cache.get_device_access_random(cache_conn, self.device_uid)
        if random_token is not None:
            self.headers.update({'X-Random': f'{random_token}'})
            self.headers.update({'Random': f'{random_token}'})


    def is_authorized(self):
        """Check if the session exists."""
        return 'Authorization' in self.headers


    def invalidate_authorization(self):
        """Invalidate the session token."""
        cache_conn = RedisPool.get_connection()
        cache.expire_device_access(cache_conn, self.device_uid)
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
                logging.warning(Locale.DEVICE_ACCESS_TOKEN_UNAVAILABLE)
                cache.set_device_timeout(cache_conn, self.device_uid)
                self.invalidate_authorization()
                return None

            is_authorized = self.update_authorization()
            if is_authorized is None:
                logging.warning(Locale.DEVICE_AUTHORIZATION_FAILED)
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
        """Process a batch of URLs using the portal GET method."""
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
        """Gets a generated channel playlist URL from channel ID."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%20http://localhost/ch/{stream_id}&series=&forced_storage=undefined&disable_ad=0&download=0&JsHttpRequest=1-xml'
        data = self.get(url)
        if data is None:
            logging.warning(Locale.DEVICE_CHANNEL_PLAYLIST_UNAVAILABLE)
            return None

        # Attempt to get the stream ID from the channel playlist command.
        stream_link = data.get('cmd')
        if not stream_link:
            error = data.get('error')
            if error == 'link_fault':
                logging.warning(Locale.DEVICE_STREAM_ID_NOT_FOUND)
                return None
            else:
                logging.warning(Locale.GENERAL_UNKNOWN_ERROR)
                return None

        return stream_link


    def get_genres(self):
        """Gets a list of genres from the portal."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml'
        genre_list = self.get(url)
        if genre_list is None:
            logging.warning(Locale.DEVICE_GENRE_LIST_UNAVAILABLE)
            return None

        return genre_list


    def get_all_channels(self):
        """Gert a list of all the channels."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml'
        data = self.get(url)
        if data is None:
            logging.warning(Locale.DEVICE_CHANNEL_LIST_UNAVAILABLE)
            return None

        channels = data.get('data') if data else None
        return channels


    def encrypt_data(self, data: dict) -> str:
        """Encrypt data using device unique key."""
        crypto = AESGCM(self.get_device_encryption_key())

        # 96-bit random nonce for AES-GCM
        nonce = os.urandom(12)
        plaintext = json.dumps(data).encode()

        ct = crypto.encrypt(nonce, plaintext, None)
        blob = nonce + ct
        return base64.urlsafe_b64encode(blob).decode().rstrip("=")  # URL safe


    def decrypt_data(self, data: str) -> dict:
        """Decrypt data using device unique key."""
        crypto = AESGCM(self.get_device_encryption_key())

        # Restore stripped padding.
        data += "=" * (-len(data) % 4)
        raw = base64.urlsafe_b64decode(data)
        nonce, ct = raw[:12], raw[12:]
        plaintext = crypto.decrypt(nonce, ct, None)
        return json.loads(plaintext)
