import datetime
import json
import uuid
from dataclasses import asdict, is_dataclass

from flask.json.provider import DefaultJSONProvider


class StrictJSONProvider(DefaultJSONProvider):
    def loads(self, s, **kwargs):
        try:
            return json.loads(s)
        except json.JSONDecodeError as e:
            raise e


class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)