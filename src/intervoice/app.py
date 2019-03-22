import os
import sys

import eliot

import intervoice.log


def main(log):
    eliot.add_global_fields(pid=os.getpid(), argv=sys.argv)
    if log:
        eliot.add_destinations(intervoice.log.json_to_file(sys.stdout))
