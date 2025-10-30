from enum import StrEnum

class ErrorMessage(StrEnum):
    DEVICE_ACCESS_TOKEN_UNAVAILABLE = 'Unable to retrieve device access token'
    DEVICE_AUTHORIZATION_FAILED = 'Device authorization check failed'
    DEVICE_AWAITING_TIMEOUT = 'Awaiting device timeout, request has been skipped'
    DEVICE_CHANNEL_LIST_SUCCESSFUL = 'Device channels have been successfully saved'
    DEVICE_CHANNEL_LIST_UNAVAILABLE = 'Unable to retrieve channel list'
    DEVICE_INVALID_RESPONSE_TEXT = 'Unable to complete request, invalid response detected'
    DEVICE_RESPONSE_UNEXPECTED_JSON = 'Received unexpected JSON data'
    DEVICE_RESPONSE_NOT_JSON = 'Received a response which is not JSON'
    DEVICE_UNAVAILABLE = 'Unable to retrieve device, check device settings and try again'
