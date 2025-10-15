import datetime

with open("version.py", "a") as f:
    build_date = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    f.write(f'\nbuild_date = "{build_date}"\n')