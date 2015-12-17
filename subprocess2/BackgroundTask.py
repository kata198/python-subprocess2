'''
    Data - This contains various Data objects associated with python-subprocess2
   
  Copyright (c) 2015 Timothy Savannah LGPL All rights reserved. See LICENSE file for more details.

    
  BackgroundTaskInfo - This is the data structure returned immediatly from Popen.runInBackground.


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

	'''

	FIELDS = ('stdoutData', 'stderrData', 'isFinished', 'returnCode', 'timeElapsed')

	def __init__(self):
		self.stdoutData = ''
		self.stderrData = ''
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

	def asDict(self):
		ret = {}
		for field in BackgroundTaskInfo.FIELDS:
			ret[field] = getattr(self, field)
		return ret

	def __repr__(self):
		return str(self.asDict())

	def keys(self):
		return BackgroundTaskInfo.FIELDS

	def waitToFinish(self, pollInterval=.1):
		while self.isFinished is False:
			time.sleep(pollInterval)

		return self.returnCode


class BackgroundTaskThread(threading.Thread):
	'''
		BackgroundTaskThread - The workhouse of a background task
	'''

	def __init__(self, pipe, taskInfo, pollInterval=.1):
		threading.Thread.__init__(self)
		self.pipe = pipe
		self.taskInfo = taskInfo
		self.pollInterval = pollInterval
		self.daemon = True # This is a background task, so if everything else is finished the program should exit

	def run(self):
		startTime = time.time()
		timeElapsed = 0
		pipe = self.pipe
		taskInfo = self.taskInfo
		pollInterval = self.pollInterval

		streams = []
		fileNoToStreamNo = {}
		if pipe.stdout:
			streams.append(pipe.stdout)
			fileNoToStreamNo[pipe.stdout.fileno()] = 1
		if pipe.stderr:
			if not pipe.stdout or pipe.stderr.fileno() != pipe.stdout.fileno(): # Ensure that stdout and stderr aren't same stream
				streams.append(pipe.stderr)
				fileNoToStreamNo[pipe.stderr.fileno()] = 2


		hasPipedIO = bool(len(streams) > 0)

		returnCode = pipe.poll()
		while returnCode is None:
			time.sleep(pollInterval)
			now = time.time()
			timeElapsed = taskInfo.timeElapsed = (now - startTime)
			if hasPipedIO:
				(readyToRead, junk1, junk2) = select.select(streams, [], [], .005)
				if readyToRead:
#					import pdb; pdb.set_trace()
					for stream in readyToRead:
						ionum = fileNoToStreamNo[stream.fileno()]
						# TODO: I don't like how this blocks on python2, python3 works very smoothly because of availability of "read1" method
						if hasattr(stream, 'read1'):
							data = stream.read1(4096).decode(sys.getdefaultencoding())
						else:
							data = stream.readline()
						if ionum == 1:
							taskInfo.stdoutData += data
						elif ionum == 2:
							taskInfo.stderrData += data

			returnCode = pipe.poll()
						
		taskInfo.returnCode = returnCode
		taskInfo.isFinished = True
