import os
import sys

import eliot

import intervoice.log


def main(log):

    if not log:
        return

    eliot.add_global_fields(pid=os.getpid(), argv=sys.argv)
    eliot.register_exception_extractor(Exception, intervoice.log.summarize_exception)
    eliot.add_destinations(intervoice.log.json_to_file(sys.stdout))
