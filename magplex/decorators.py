import logging
from functools import wraps
from http import HTTPStatus

from flask import g, redirect, request

from magplex import PostgresConnection, users
from magplex.utilities.error import ErrorResponse

from magplex.utilities.localization import Locale


class AuthMethod:
    API = 'api'
    SESSION = 'session'
    ALL = 'all'


def authorize_route(*, auth_method=AuthMethod.ALL, force_redirect=False):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            # Attempt to get the user from an API key.
            user_authenticated = False
            api_key = request.headers.get('X-Api-Key')
            if api_key and auth_method in (AuthMethod.API, AuthMethod.ALL):
                with PostgresConnection() as conn:
                    user_profile = users.database.get_user_key(conn, api_key)
                    if user_profile:
                        g.user_uid = user_profile.user_uid
                        user_device_profile = users.database.get_device_profile_by_user(conn, user_profile.user_uid)
                        g.device_uid = user_device_profile.device_uid if user_device_profile else None
                        user_authenticated = True

            # Attempt to get the user from a session.
            session_uid = request.cookies.get('session_uid')
            if session_uid and auth_method in (AuthMethod.SESSION, AuthMethod.ALL):
                with PostgresConnection() as conn:
                    user_session = users.database.get_user_session(conn, session_uid)
                    if user_session is not None:
                        g.user_session = user_session
                        g.user_uid = user_session.user_uid
                        user_device_profile = users.database.get_device_profile_by_user(conn, user_session.user_uid)
                        g.device_uid = user_device_profile.device_uid if user_device_profile else None
                        user_authenticated = True

            if not user_authenticated:
                if force_redirect:
                    return redirect('/login')
                else:
                    return ErrorResponse(Locale.GENERAL_INVALID_CREDENTIALS, HTTPStatus.FORBIDDEN)

            return func(*args, **kwargs)
        return decorated
    return decorator
