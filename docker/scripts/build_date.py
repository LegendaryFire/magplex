import datetime
from zoneinfo import ZoneInfo

with open("/opt/magplex/version.py", "a") as f:
    build_date = datetime.datetime.now(ZoneInfo("America/Vancouver")).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
    f.write(f'\nbuild_date = "{build_date}"\n')