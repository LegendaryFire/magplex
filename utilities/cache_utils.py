import os
from flask import current_app
from cache import ttl_cache
from utilities import parser


@ttl_cache(ttl_seconds=int(os.getenv('CACHE_EXPIRATION')))
def get_channel_guide():
    channels = current_app.stb.get_channel_list()
    guides = current_app.stb.get_channel_guide()
    guide = parser.build_channel_guide(channels, guides)
    return guide