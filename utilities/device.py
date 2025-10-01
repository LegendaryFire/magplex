import json
import logging
from dataclasses import dataclass
from http import HTTPStatus

import requests


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
    def __init__(self, profile: Profile):
        self.authorized = True
        self.session = requests.session()
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

    def get_token(self):
        """Gets the authentication token for the session."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=stb&action=handshake&token=&JsHttpRequest=1-xml'
        self.headers.pop('Authorization')  # Remove the old authentication header.
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
            self.headers.pop('Authorization')  # Clear the authentication header on failure.
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
            if not data and (not isinstance(data, list) or not isinstance(data, dict)):
                logging.warning("Unknown response data received.")
                return None
        except json.JSONDecodeError:
            self.authorized = False
            logging.warning("Unable to decode response data.")
            return None

        return data

    def get_channel(self, stream_id):
        """Gets a generated channel URL from stream ID."""
        url = f'http://{self.profile.portal}/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%20http://localhost/ch/{stream_id}&series=&forced_storage=undefined&disable_ad=0&download=0&JsHttpRequest=1-xml',
        data = self.get(url)
        return data.get('cmd') if data else None