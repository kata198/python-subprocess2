#!/usr/bin/env python

# A module for sleeping and testing return codes, so tests run on windows too.


import time
import signal
import sys


DROP_SIGTERM = 250

def handle_sigterm(*args):
    # Should support the various OS's to return the correct value
    global sigtermReturnCode
    if sigtermReturnCode == DROP_SIGTERM:
        time.sleep(float(sys.argv[1]))
        return

    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(sigtermReturnCode)

#    os.kill(os.getpid(), signal.SIGTERM)
    return sigtermReturnCode



if __name__ == '__main__':
    global sigtermReturnCode

    try:
        returnCode = int(sys.argv[2])
    except KeyError:
        returnCode = 0

    try:
        sigtermReturnCode = int(sys.argv[3])
    except:
        sigtermReturnCode = returnCode

    signal.signal(signal.SIGTERM, handle_sigterm)
    
    time.sleep(float(sys.argv[1]))

    sys.exit(returnCode)
