import os
import sys

import eliot

import intervoice.log


def main(should_log):

    if not should_log:
        return

    eliot.register_exception_extractor(Exception, intervoice.log.summarize_exception)
    eliot.add_destinations(intervoice.log.json_to_file(sys.stdout))
