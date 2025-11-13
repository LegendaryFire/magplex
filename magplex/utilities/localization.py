from enum import StrEnum


class Locale(StrEnum):
    # General Localization
    GENERAL_EXPECTED_JSON = 'Content type is not application/json or the JSON body is malformed'
    GENERAL_INVALID_CREDENTIALS = 'Invalid credentials, please try again'
    GENERAL_MISSING_ENDPOINT_PARAMETERS = 'Missing mandatory URL parameters or data'
    GENERAL_MISSING_REQUIRED_FIELDS = 'Missing or invalid required fields, please try again'
    GENERAL_UNKNOWN_ERROR = 'An unknown error has occurred'
    GENERAL_TIMEOUT_ERROR = 'Network request timed out'

    # Device Localization
    DEVICE_ACCESS_TOKEN_UNAVAILABLE = 'Unable to retrieve device access token'
    DEVICE_AUTHORIZATION_FAILED = 'Device authorization check failed'
    DEVICE_AWAITING_TIMEOUT = 'Awaiting device timeout, request has been skipped'
    DEVICE_CHANNEL_LIST_SUCCESSFUL = 'Device channels have been successfully saved'
    DEVICE_CHANNEL_LIST_UNAVAILABLE = 'Unable to retrieve channel list'
    DEVICE_CHANNEL_PLAYLIST_UNAVAILABLE = 'Unable to retrieve channel playlist'
    DEVICE_CHANNEL_STREAM_MISMATCH = 'Stream ID did not match the one provided'
    DEVICE_GENRE_LIST_UNAVAILABLE = 'Unable to retrieve genre list'
    DEVICE_INVALID_RESPONSE_CODE = 'Invalid response code received'
    DEVICE_INVALID_RESPONSE_TEXT = 'Invalid response content received'
    DEVICE_NON_EXISTENT_ERROR = 'Cannot continue. Device does not exist'
    DEVICE_NOT_REGISTERED_TEXT = 'Device is not registered, or does not have an active subscription'
    DEVICE_RESPONSE_UNEXPECTED_JSON = 'Received unexpected JSON data'
    DEVICE_RESPONSE_NOT_JSON = 'Received a response which is not JSON'
    DEVICE_STREAM_ID_NOT_FOUND = 'Stream ID does not exist'
    DEVICE_STREAM_SEGMENT_FAILED = 'Unable to retrieve stream segment'
    DEVICE_UNAVAILABLE = 'Unable to retrieve device, check device settings and try again'
    DEVICE_UNKNOWN_CHANNEL = 'Unable to locate specified channel, please try again'
    DEVICE_UNKNOWN_STREAM = 'Unable to locate specified stream, please try again'
    DEVICE_INVALID_DECRYPTED_DATA = 'Invalid decrypted data'

    # Encoder Localization
    ENCODER_NO_SUPPORTED_CODEC = 'Unable to find supported codec, falling back to remuxing'
    ENCODER_REMUXING_NO_PRESET = 'Encoder preset does not exist when remuxing'
    ENCODER_REMUXING_NO_NAME = 'Encoder name does not exist when remuxing'

    # Logging Localization
    LOG_FILE_NOT_FOUND = 'Could not find log file'

    # Task Localization
    TASK_CHANNEL_GUIDE_TRIGGERED = 'Manually triggered channel guide refresh'
    TASK_CONFLICTING_JOB_IGNORED = 'Scheduler conflicting ID error ignored'
    TASK_JOB_ADDED_SUCCESSFULLY = 'Job added to the job pool'
    TASK_RUNNING_CHANNEL_GUIDE_REFRESH = 'Running device channel guide refresh task'
    TASK_RUNNING_CHANNEL_LIST_REFRESH = 'Running device channel list refresh task'

    # User Interface Localization
    UI_USERNAME_CONTAINS_SPACES = "New username can't contain spaces"
    UI_USERNAME_DIDNT_CHANGE = 'The new username is the same as current'
    UI_PASSWORD_REQUIREMENT_NOT_MET = 'New password must be at least 8 characters long'
    UI_PASSWORD_DOESNT_MATCH = 'The new passwords do not match, please try again'

    def __call__(self, **kwargs):
        if not kwargs:
            return self.value
        processed = {}
        for k, v in kwargs.items():
            s = str(v)
            if len(s) > 100:
                s = s[:100] + "…"
            processed[k] = s
        extra = ", ".join(f"{k}={v}" for k, v in processed.items())
        return f"{self.value} ({extra})"