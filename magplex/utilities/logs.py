import werkzeug


def initialize():
    # Disable color logging style.
    werkzeug.serving._log_add_style = False
