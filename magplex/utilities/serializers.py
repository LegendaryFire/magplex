import orjson
from flask.json.provider import JSONProvider


class ORJSONProvider(JSONProvider):
    def loads(self, s, **kwargs):
        return orjson.loads(s)

    def dumps(self, obj, **kwargs):
        return orjson.dumps(obj).decode('utf-8')
