import datetime
import json
import uuid
from dataclasses import asdict, is_dataclass


class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)