'''
    python-subprocess2
   
  Copyright (c) 2015-2016 Timothy Savannah LGPL All rights reserved. See LICENSE file for more details.

  This module provides extensions to the standard "subprocess" module
  Importing this module modifies the global subprocess module. You can use it like:

    from subprocess2 import Popen

  or

    import subprocess2

    from subprocess import Popen

    
'''

import time

# Make sure import * imports the same set as subprocess. If we define extra modules or whatever later they will be added here too
__origDefined = set(locals().keys())

DEFAULT_POLL_INTERVAL = .05 # Number of seconds as default for polling interval

SUBPROCESS2_DEFAULT_TERMINATE_TO_KILL_SECONDS = 1.5

SUBPROCESS2_PROCESS_COMPLETED  = 0
SUBPROCESS2_PROCESS_TERMINATED = 1
SUBPROCESS2_PROCESS_KILLED     = 2


subprocess2_version = '2.0.1'
subprocess2_version_tuple = (2, 0, 1)


from subprocess import * # I know, bad form to import *, but ensures that you can use this interchangably with the upstream subprocess

__subprocessDefined = set(locals().keys()).difference(__origDefined)
__subprocessDefined -= set(['__origDefined'])

__all__ = list(__subprocessDefined) + ['Simple', 'SimpleCommandFailure']

# Apply our global updates
import subprocess
subprocess.SUBPROCESS2_PROCESS_COMPLETED = SUBPROCESS2_PROCESS_COMPLETED
subprocess.SUBPROCESS2_PROCESS_TERMINATED = SUBPROCESS2_PROCESS_TERMINATED
subprocess.SUBPROCESS2_PROCESS_KILLED = SUBPROCESS2_PROCESS_KILLED
subprocess.DEFAULT_POLL_INTERVAL = DEFAULT_POLL_INTERVAL
subprocess.SUBPROCESS2_DEFAULT_TERMINATE_TO_KILL_SECONDS = SUBPROCESS2_DEFAULT_TERMINATE_TO_KILL_SECONDS
subprocess.subprocess2_version = subprocess2_version
subprocess.subprocess2_version_tuple = subprocess2_version_tuple

__version__ = subprocess2_version # Only __version__ in subprocess2 module, don't backpatch this.

from .BackgroundTask import BackgroundTaskInfo

from .simple import Simple, SimpleCommandFailure

subprocess.Simple = Simple

def waitUpTo(self, timeoutSeconds, pollInterval=DEFAULT_POLL_INTERVAL):
    '''
        Popen.waitUpTo - Wait up to a certain number of seconds for the process to end.

            @param timeoutSeconds <float> - Number of seconds to wait

            @param pollInterval <float> (default .05) - Number of seconds in between each poll

            @return - Returncode of application, or None if did not terminate.
    '''
    i = 0
    numWaits = timeoutSeconds / float(pollInterval)

    ret = self.poll()
    if ret is None:
        while i < numWaits:
            time.sleep(pollInterval)
            ret = self.poll()
            if ret is not None:
                break
            i += 1

    return ret

Popen.waitUpTo = waitUpTo

def waitOrTerminate(self, timeoutSeconds, pollInterval=DEFAULT_POLL_INTERVAL, terminateToKillSeconds=SUBPROCESS2_DEFAULT_TERMINATE_TO_KILL_SECONDS):
    '''
        waitOrTerminate - Wait up to a certain number of seconds for the process to end.

            If the process is running after the timeout has been exceeded, a SIGTERM will be sent. 
            Optionally, an additional SIGKILL can be sent after some configurable interval. See #terminateToKillSeconds doc below

            @param timeoutSeconds <float> - Number of seconds to wait

            @param pollInterval <float> (default .05)- Number of seconds between each poll

            @param terminateToKillSeconds <float/None> (default 1.5) - If application does not end before #timeoutSeconds , terminate() will be called.

                * If this is set to None, an additional #pollInterval sleep will occur after calling .terminate, to allow the application to cleanup. returnCode will be return of app if finished, or None if did not complete.
                * If this is set to 0, no terminate signal will be sent, but directly to kill. Because the application cannot trap this, returnCode will be None.
                * If this is set to > 0, that number of seconds maximum will be given between .terminate and .kill. If the application does not terminate before KILL, returnCode will be None.

            Windows Note -- On windows SIGTERM and SIGKILL are the same thing.

            @return dict { 'returnCode' : <int or None> , 'actionTaken' : <int mask of SUBPROCESS2_PROCESS_*> }
                Returns a dict representing results: 
                    "returnCode" matches return of application, or None per #terminateToKillSeconds doc above.
                    "actionTaken" is a mask of the SUBPROCESS2_PROCESS_* variables. If app completed normally, it will be SUBPROCESS2_PROCESS_COMPLETED, otherwise some mask of SUBPROCESS2_PROCESS_TERMINATED and/or SUBPROCESS2_PROCESS_KILLED
    '''
    returnCode = self.waitUpTo(timeoutSeconds, pollInterval)
    actionTaken = SUBPROCESS2_PROCESS_COMPLETED


    if returnCode is None:
        if terminateToKillSeconds is None:
            self.terminate()
            actionTaken |= SUBPROCESS2_PROCESS_TERMINATED

            time.sleep(pollInterval) # Give a chance to cleanup
            returnCode = self.poll()

        elif terminateToKillSeconds == 0:
            self.kill()
            actionTaken |= SUBPROCESS2_PROCESS_KILLED

            time.sleep(.01)  # Give a chance to happen
            self.poll() # Don't defunct

            returnCode = None
        else:
            self.terminate()
            actionTaken |= SUBPROCESS2_PROCESS_TERMINATED

            returnCode = self.waitUpTo(terminateToKillSeconds, pollInterval)
            if returnCode is None:
                actionTaken |= SUBPROCESS2_PROCESS_KILLED
                self.kill()
                time.sleep(.01)
                self.poll() # Don't defunct

    return {
        'returnCode' : returnCode,
        'actionTaken' : actionTaken
    }

Popen.waitOrTerminate = waitOrTerminate


def runInBackground(self, pollInterval=.1, encoding=False):
    '''
        runInBackground - Create a background thread which will manage this process, automatically read from streams, and perform any cleanups

          The object returned is a "BackgroundTaskInfo" object, and represents the state of the process. It is updated automatically as the program runs,
            and if stdout or stderr are streams, they are automatically read from and populated into this object.

         @see BackgroundTaskInfo for more info or https://htmlpreview.github.io/?https://raw.githubusercontent.com/kata198/python-subprocess2/master/doc/subprocess2.BackgroundTask.html

        @param pollInterval - Amount of idle time between polling
        @param encoding - Default False. If provided, data will be decoded using the value of this field as the codec name (e.x. "utf-8"). Otherwise, data will be stored as bytes.
    '''
        
    from .BackgroundTask import BackgroundTaskThread

    taskInfo = BackgroundTaskInfo(encoding)
    thread = BackgroundTaskThread(self, taskInfo, pollInterval, encoding)

    thread.start()
    #thread.run()  # Uncomment to use pdb debug (will not run in background)
    return taskInfo

Popen.runInBackground = runInBackground

# vim: ts=4 sw=4 expandtab :
