import json
from dataclasses import is_dataclass, asdict

class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)