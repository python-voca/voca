import os
import sys

import eliot

import voca.log


def main(should_log: bool) -> None:
    """
    Set up the app execution environment.

    Args:
        should_log: Enable or disable logging.

    """

    if not should_log:
        return

    eliot.register_exception_extractor(Exception, voca.log.summarize_exception)
    eliot.add_destinations(voca.log.json_to_file(sys.stdout))
