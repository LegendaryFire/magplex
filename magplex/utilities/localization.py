from enum import StrEnum


class ErrorMessage(StrEnum):
    GENERAL_MISSING_ENDPOINT_PARAMETERS = 'Missing mandatory URL parameters or data'
    GENERAL_UNKNOWN_ERROR = 'An unknown error has occurred'
    DEVICE_ACCESS_TOKEN_UNAVAILABLE = 'Unable to retrieve device access token'
    DEVICE_AUTHORIZATION_FAILED = 'Device authorization check failed'
    DEVICE_AWAITING_TIMEOUT = 'Awaiting device timeout, request has been skipped'
    DEVICE_CHANNEL_LIST_SUCCESSFUL = 'Device channels have been successfully saved'
    DEVICE_CHANNEL_LIST_UNAVAILABLE = 'Unable to retrieve channel list'
    DEVICE_CHANNEL_PLAYLIST_UNAVAILABLE = 'Unable to retrieve channel playlist'
    DEVICE_CHANNEL_STREAM_MISMATCH = 'Stream ID did not match the one provided'
    DEVICE_GENRE_LIST_UNAVAILABLE = 'Unable to retrieve genre list'
    DEVICE_INVALID_RESPONSE_TEXT = 'Unable to complete request, invalid response detected'
    DEVICE_RESPONSE_UNEXPECTED_JSON = 'Received unexpected JSON data'
    DEVICE_RESPONSE_NOT_JSON = 'Received a response which is not JSON'
    DEVICE_STREAM_ID_NOT_FOUND = 'Stream ID does not exist'
    DEVICE_STREAM_SEGMENT_FAILED = 'Unable to retrieve stream segment'
    DEVICE_UNAVAILABLE = 'Unable to retrieve device, check device settings and try again'
    DEVICE_UNKNOWN_CHANNEL = 'Unable to locate specified channel, please try again'
    DEVICE_UNKNOWN_STREAM = 'Unable to locate specified stream, please try again'
    DEVICE_INVALID_DECRYPTED_DATA = 'Invalid decrypted data'
    TASK_CHANNEL_GUIDE_TRIGGERED = 'Manually triggered channel guide refresh'
