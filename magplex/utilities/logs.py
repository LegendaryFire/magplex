import logging

import werkzeug

from magplex.utilities.variables import Environment


def initialize():
    # Disable color logging style.
    werkzeug.serving._log_add_style = False

    # Set up global logging configuration
    handlers = [logging.StreamHandler()]
    level = logging.DEBUG if Environment.DEBUG else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s]: %(message)s', handlers=handlers)