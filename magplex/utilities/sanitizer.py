def sanitize_string(value, *, lower=False, upper=False, strip=True, max_length=None):
    if value is None:
        return None
    value = str(value)
    if strip:
        value = value.strip()
    if not value:
        return None
    if max_length is not None and len(value) > max_length:
        value = value[:max_length]
    if lower:
        value = value.lower()
    elif upper:
        value = value.upper()
    return value


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


def sanitize_bool(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    truthy = {"1", "true", "yes", "on", "y", "t"}
    falsy  = {"0", "false", "no", "off", "n", "f"}
    if value in truthy:
        return True
    if value in falsy:
        return False
    return False
