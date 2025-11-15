import re
from http import HTTPStatus
import requests

from magplex.utilities import sanitizer


def validate_portal_referer(portal_link):
    """Validates the portal URL, and returns the referer URL if successful."""
    response = requests.get(portal_link, allow_redirects=True, stream=True, timeout=5)
    if response.status_code != HTTPStatus.OK:
        return None
    return response.url


def validate_portal_loader(referer_link):
    """Validates the portal URL, and returns the loader URL if successful."""
    response = requests.get(referer_link, allow_redirects=True, stream=True, timeout=5)
    if response.status_code != HTTPStatus.OK:
        return None

    referer_link = response.url.rstrip('/')
    common_link = f'{referer_link}/xpcom.common.js'
    response = requests.get(common_link)
    if response.status_code != HTTPStatus.OK:
        return None

    size = 0
    chunks = []
    for chunk in response.iter_content(4096, decode_unicode=True):
        if not chunk:
            break
        size += len(chunk)
        if size > 500_000:
            return None
        chunks.append(chunk)

    ajax_loader = None
    for line in response.text.splitlines():
        line = line.lstrip()
        if line.startswith(('this.ajax_loader =', 'this.ajax_loader=')):
            ajax_loader = line
            break
    if ajax_loader is None:
        return None

    # Clean up the variable.
    remove_list = ["this.ajax_loader", "=", "'", "+", ";"]
    for remove in remove_list:
        ajax_loader = ajax_loader.replace(remove, '')
    ajax_loader = ajax_loader.strip()

    pattern = re.compile(r'(http?|https?)://([^/]*)/([\w/]+)*/(.)*')
    match = pattern.match(referer_link)
    if match is None:
        return None

    result = {
        'portal_protocol': match.group(1),
        'portal_ip': match.group(2),
        'portal_path': match.group(3)
    }
    variables = re.findall(r"this\.(\w+)", ajax_loader)
    for var in variables:
        if var in variables and result[var] is not None:
            ajax_loader = ajax_loader.replace(f"this.{var}", result[var])
        else:
            return None

    ajax_loader = sanitizer.sanitize_url(ajax_loader)
    if ajax_loader:
        return ajax_loader
    return None