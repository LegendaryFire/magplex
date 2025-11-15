from http import HTTPStatus

import requests
from py_mini_racer import MiniRacer


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

    js = MiniRacer()
    common_script = response.text
    js.eval(common_script.strip(), timeout=500, max_memory=5_000_000)
    js.eval("""
        const document = Object();
        function _debug() {}
        function getPortalUrl(portalUrl) {
            Object.defineProperty(document, "URL", {value: portalUrl, writable: true, configurable: true});
            const xpCom = new common_xpcom();
            xpCom.get_server_params();
            return xpCom.ajax_loader;
        }
    """, timeout=500, max_memory=5_000_000)

    loader_url = js.eval(f"getPortalUrl('{common_link}');", timeout=500, max_memory=5_000_000)
    if loader_url is not None:
        return loader_url
    return None
