'''
  BackgroundTask.py - This contains the implementation and data storage for background tasks.
   
  Copyright (c) 2015-2016 Timothy Savannah LGPLv2 All rights reserved. See LICENSE file for more details.

    
  BackgroundTaskInfo - This is the data structure returned immediately from Popen.runInBackground.

  _py_read1 - Pure-python implementation of read1 method for non-blocking stream I/O 

  BackgroundTaskThread - The work implementation of the thread spawned by Popen.runInBackground

'''

# vim: ts=4 sw=4 expandtab :

import select
import sys
import threading
import time

class BackgroundTaskInfo(object):
    '''
        BackgroundTaskInfo - Represents a task that was sent to run in the background. Will be updated as the status of that process changes.

            Can be used like an object or a dictionary.

        This object populates its data automatically as the program runs in the background, managed by a thread.

        Optional arg "encoding" - If provided, data will be automatically decoded using this codec. Otherwise, data will be stored as bytes.

        FIELDS:

            stdoutData - Bytes read automatically from stdout, if stdout was a pipe, or from stderr if stderr was set to subprocess.STDOUT
            stderrData - Bytes read automatically from stderr, if different pipe than stdout.
            isFinished - False while the background application is running, True when it completes.
            returnCode - None if the program has not completed, otherwise the numeric return code.
            timeElapsed - Float of how many seconds have elapsed since the last update (updates happen very close to the "pollInterval" provided when calling runInBackground)

    '''

    # All fields for export
    FIELDS = ('stdoutData', 'stderrData', 'isFinished', 'returnCode', 'timeElapsed', 'encoding')

    def __init__(self, encoding=False):
        self.stdoutData = b''
        self.stderrData = b''
        self.encoding = encoding
        if encoding:
            try:
                self.stdoutData = self.stdoutData.decode(encoding)
                self.stderrData = self.stderrData.decode(encoding)
            except Exception as e:
                raise ValueError('Cannot decode using codec %s: %s' %(repr(encoding), str(e)))
        self.isFinished = False
        self.returnCode = None
        self.timeElapsed = 0


    def __contains__(self, name):
        return bool(name in BackgroundTaskInfo.FIELDS)

    def __getitem__(self, name):
        if not name in self:
            raise KeyError("%s is not a field of BackgroundTaskInfo. Possible fields are: %s" %(name, ', '.join(BackgroundTaskInfo.FIELDS)))
        return getattr(self, name)

    def __setitem__(self, name, value):
        if not name in self:
            raise KeyError("%s is not a field of BackgroundTaskInfo. Possible fields are: %s" %(name, ', '.join(BackgroundTaskInfo.FIELDS)))
        setattr(self, name, value)


    def __repr__(self):
        return str(self.asDict())

    def keys(self):
        return BackgroundTaskInfo.FIELDS

    def items(self):
        return self.asDict().items()


    def asDict(self):
        '''
            asDict - Returns a copy of the current state as a dictionary. This copy will not be updated automatically.

            @return <dict> - Dictionary with all fields in BackgroundTaskInfo.FIELDS
        '''
        ret = {}
        for field in BackgroundTaskInfo.FIELDS:
            ret[field] = getattr(self, field)
        return ret

    def waitToFinish(self, timeout=None, pollInterval=.1):
        '''
            waitToFinish - Wait (Block current thread), optionally with a timeout, until background task completes.

            @param timeout <None/float> - None to wait forever, otherwise max number of seconds to wait
            @param pollInterval <float> - Seconds between each poll. Keep high if interactivity is not important, low if it is.

            @return - None if process did not complete (and timeout occured), otherwise the return code of the process is returned.
        '''
        if timeout is None:
            while self.isFinished is False:
                time.sleep(pollInterval)
        else:
            sleptFor = 0
            while self.isFinished is False and sleptFor < timeout:
                time.sleep(pollInterval)
                sleptFor += pollInterval

        return self.returnCode


def _py_read1(fileObj, maxBuffer):
    '''
        _py_read1 - Pure python version of "read1", which allows non-blocking I/O on a potentially unfinished or  non-newline-ending stream. 

        @param maxBuffer - Max buffer size

        @return - All data available on stream, regardless of newlines
    '''
    i = 0
    ret = []
    while i < maxBuffer:
        c = fileObj.read(1)
        if c == '':
            # Stream has been closed
            break
        i += 1
        ret.append(c)
        # Use a very low timeout so we only grab more data if it's immediately available.
        (readyToRead, junk1, junk2) = select.select([fileObj], [], [], .00001)
        if not readyToRead:
            break

    return ''.join(ret)


class BackgroundTaskThread(threading.Thread):
    '''
        BackgroundTaskThread - INTERNAL. The workhouse of a background task. This runs the actual task and populates the BackgroundTaskInfo object
    '''


    def __init__(self, pipe, taskInfo, pollInterval=.1, encoding=False):
        threading.Thread.__init__(self)
        self.pipe = pipe
        self.taskInfo = taskInfo
        self.pollInterval = pollInterval
        self.encoding = encoding
        self.daemon = True # This is a background task, so if everything else is finished the program should exit

    def run(self):
        startTime = time.time()
        timeElapsed = 0
        pipe = self.pipe
        taskInfo = self.taskInfo
        pollInterval = self.pollInterval
        encoding = self.encoding

        # All streams we are going to manage
        streams = []

        # fileNoToStreamNo - This is a map of the streams to a number. That number is 1 for stdout, and 2 for stderr.
        fileNoToStreamNo = {}

        # This is a flag we will set if read1 is missing on the file object (like python 2.7) and we need to do our own.
        simulateRead1 = False

        if pipe.stdout:
            streams.append(pipe.stdout)
            fileNoToStreamNo[pipe.stdout.fileno()] = 1
            if not hasattr(pipe.stdout, 'read1'):
                simulateRead1 = True

        if pipe.stderr:
            if not pipe.stdout or pipe.stderr.fileno() != pipe.stdout.fileno(): # Ensure that stdout and stderr aren't same stream
                streams.append(pipe.stderr)
                fileNoToStreamNo[pipe.stderr.fileno()] = 2
                if not hasattr(pipe.stderr, 'read1'):
                    simulateRead1 = True


        if len(streams) > 0:
            hasPipedIO = True
            # Try to make the select polling time to be a reasonable value.
            #   the idea is to allow at most a 1% variance in refresh time,
            #   while still not thrasing resources and constant switching.
            selectInterval = min(.2, pollInterval / 100.0)
            selectInterval = max(.000005, selectInterval)
        else:
            hasPipedIO = False

        # Poll here and see if we are already done before starting. We don't have to worry about missing a read of data 
        #   on the stream, because the output would still be blocking and thus child could not exit.
        returnCode = pipe.poll()
        while returnCode is None:
            time.sleep(pollInterval)

            # timeElapsed needs to be calculated here to be accurate, since so much beyond counting-and-sleeping is happening.
            timeElapsed = taskInfo.timeElapsed = (time.time() - startTime)

            if hasPipedIO:
                # Automaticly read stdout/stderr streams if they were set
                (readyToRead, junk1, junk2) = select.select(streams, [], [], selectInterval)
                if readyToRead:
                    for stream in readyToRead:
                        # Determine which stream we were returned by mapping fd to stream number
                        ionum = fileNoToStreamNo[stream.fileno()]

                        # Use read method that won't block on unfinished/un-newlined data on stream
                        if simulateRead1 is False:
                            data = stream.read1(4096)
                        else:
                            data = _py_read1(stream, 4096)

                        if encoding:
                            data = data.decode(encoding)

                        # Append into correct location
                        if ionum == 1:
                            taskInfo.stdoutData += data
                        elif ionum == 2:
                            taskInfo.stderrData += data

            returnCode = pipe.poll()
        
        # sub process has completed, close out.
        taskInfo.returnCode = returnCode
        taskInfo.isFinished = True

