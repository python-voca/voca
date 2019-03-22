import os
import sys

import eliot

from intervoice import log


def main():
    eliot.add_global_fields(pid=os.getpid(), argv=sys.argv)
    eliot.add_destinations(log.json_to_file(sys.stdout))
