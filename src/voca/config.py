import os
import pathlib

import appdirs

from voca import utils


@utils.public
def get_config_dir() -> pathlib.Path:
    """Get the location of voca user config directory."""
    return pathlib.Path(
        os.environ.get("VOCA_CONFIG_DIR") or appdirs.user_config_dir("voca")
    )
