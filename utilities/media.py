from enum import StrEnum


class MimeType(StrEnum):
    M3U8_APPLE = 'application/vnd.apple.mpegurl'
    M3U8_AUDIO = 'audio/x-mpegurl'
    JSON = 'application/json'

    @classmethod
    def all_types(cls):
        return list(cls)

    @classmethod
    def m3u8_types(cls):
        return [cls.M3U8_APPLE, cls.M3U8_AUDIO]