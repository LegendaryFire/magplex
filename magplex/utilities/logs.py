import logging
import os

import werkzeug

from magplex.utilities.environment import Variables


def initialize():
    # Disable color logging style.
    werkzeug.serving._log_add_style = False

    # Create the logging directory if it doesn't exist.
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Set up global logging configuration
    handlers = [logging.StreamHandler(), logging.FileHandler(Variables.BASE_LOG)]
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s', handlers=handlers)
