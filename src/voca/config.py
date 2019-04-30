import os

import appdirs


def get_config_dir():
    return os.environ.get("VOCA_CONFIG_DIR") or appdirs.user_config_dir("voca")
