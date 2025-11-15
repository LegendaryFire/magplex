from urllib.parse import urlunparse, urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def sanitize_string(value, *, lower=False, upper=False, strip=True, max_length=None, empty=False):
    if value is None:
        return None if not empty else ''
    value = str(value)
    if strip:
        value = value.strip()
    if not value:
        return None if not empty else ''
    if max_length is not None and len(value) > max_length:
        value = value[:max_length]
    if lower:
        value = value.lower()
    elif upper:
        value = value.upper()
    return value


def sanitize_url(value, *, require_scheme=True, allowed_schemes=("http", "https"), strip=True, empty=False):
    if value is None:
        return None if not empty else ''
    value = str(value)
    if strip:
        value = value.strip()
    if not value:
        return None if not empty else ''

    parsed = urlparse(value)
    if require_scheme and not parsed.scheme:
        return None
    if parsed.scheme and allowed_schemes and parsed.scheme.lower() not in allowed_schemes:
        return None
    if not parsed.netloc:
        return None

    scheme = parsed.scheme.lower() if parsed.scheme else ""
    netloc = parsed.netloc.lower()
    return urlunparse((scheme, netloc, parsed.path or "", parsed.params or "", parsed.query or "", parsed.fragment or ""))

def sanitize_int(value, *, minimum=None, maximum=None):
    if value is None:
        return None
    try:
        value = int(value)
    except (ValueError, TypeError):
        return None
    if minimum is not None and value < minimum:
        return minimum
    if maximum is not None and value > maximum:
        return maximum
    return value


def sanitize_bool(value, empty=False):
    if value is None:
        return False if not empty else None
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    truthy = {"1", "true", "yes", "on", "y", "t"}
    falsy  = {"0", "false", "no", "off", "n", "f"}
    if value in truthy:
        return True
    if value in falsy:
        return False
    return False if not empty else None


def sanitize_timezone(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError:
        return None
    return value
