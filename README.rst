python-subprocess2
==================

Extensions on the python subprocess module. Importing subprocess2 will extend the global "subprocess" module (only additions, no modifications, so it's safe).

You can also import and use subprocess2 instead of the subprocess module. Doing a global extension allows your application or library to utilize the extensions without requiring modification of other codebases. In example, if you have a library that is opening a pipe and passing it to your application, it does not need to be modified for you to use the additional Popen methods on the object you received.


Simply installing the subprocess2 module does not do anything to the parent subprocess module, until it has been imported, and then only additions are made.




PyDoc Reference
---------------

PyDoc Reference for extended subprocess modules can be found at: http://htmlpreview.github.io/?https://github.com/kata198/python-subprocess2/blob/master/doc/subprocess2.html





Popen
=====

Additions to Popen class:




**waitUpTo**


This method adds the ability to specify a timeout when waiting for a subprocess to complete.


    Popen.waitUpTo (timeoutSeconds, pollInterval) - Wait up to a certain number of seconds for the process to end.


        @param timeoutSeconds <float> - Number of seconds to wait

        @param pollInterval <float> (default .05) - Number of seconds in between each poll


        @return - Returncode of application, or None if did not terminate.





**waitOrTerminate**


This method allows specifying a timeout, like waitUpTo, but will also handle terminating or killing the application if it exceeds the timeout (see documentation below).

	Popen.waitOrTerminate(self, timeoutSeconds, pollInterval=DEFAULT_POLL_INTERVAL, terminateToKillSeconds=SUBPROCESS2_DEFAULT_TERMINATE_TO_KILL_SECONDS):

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

Background Task Management
==========================

One of the benefits to modern computing is the ability to multitask. Your application may want to start several sub processes at once, and have them all collecting output simultaneously. The standard python "subprocess" module does not provide a simple approach through it's API to do this.

subprocess2 extends the Popen module by adding the notion of a "Background Task." When you call "runInBackground" on a pipe object, it will create and start a thread to automatically handle that process.

Calling "runInBackground" on a pipe returns a "BackgroundTaskInfo" option, which is dynamically updated as the status the subprocess progresses. 

If you have open streams (stdout, stderr), they will automatically be read in non-blocking fashion into "stdoutData" and "stderrData" respectively on that object. 

When the subprocess terminates, the "returnCode" field will be set, and "isFinished" will be marked True.

By default, data will be stored as bytes. To decode with a specific encoding (e.x. utf-8), pass the codec name as the "encoding" argument.


You can use this to farm out 10 processes quickly, collect all their data, and wait for them to complete. Other uses may be long-running associated proccesses, such as several searches collecting data, all being used to update a display.


Method Signature:

	def runInBackground(self, pollInterval=.1, encoding=False):

		'''

			runInBackground - Create a background thread which will manage this process, automatically read from streams, and perform any cleanups



			  The object returned is a "BackgroundTaskInfo" object, and represents the state of the process. It is updated automatically as the program runs,

				and if stdout or stderr are streams, they are automatically read from and populated into this object.


			 @see BackgroundTaskInfo for more info or https://htmlpreview.github.io/?https://raw.githubusercontent.com/kata198/python-subprocess2/master/doc/subprocess2.BackgroundTask.html


			@param pollInterval - Amount of idle time between polling

			@param encoding - Default False. If provided, data will be decoded using the value of this field as the codec name (e.x. "utf-8"). Otherwise, data will be stored as bytes.

		'''


Object returned:


	class BackgroundTaskInfo(object):

		'''

			BackgroundTaskInfo - Represents a task that was sent to run in the background. Will be updated as the status of that process changes.


				Can be used like an object or a dictionary.


			This object populates its data automatically as the program runs in the background, managed by a thread.


			FIELDS:


				stdoutData - Bytes read automatically from stdout, if stdout was a pipe, or from stderr if stderr was set to subprocess.STDOUT

				stderrData - Bytes read automatically from stderr, if different pipe than stdout.

				isFinished - False while the background application is running, True when it completes.

				returnCode - None if the program has not completed, otherwise the numeric return code.

				timeElapsed - Float of how many seconds have elapsed since the last update (updates happen very close to the "pollInterval" provided when calling runInBackground)


		'''


So for example:

	import subprocess2 as subprocess


	pipe1 = subprocess.Popen(......, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	pipe2 = subprocess.Popen(......, stdout=subprocess.PIPE)


	pipe1Info = pipe1.runInBackground()

	pipe2Info = pipe2.runInBackground()


will have two processes running in the background, collecting their output automatically, and cleaning up automatically.


If you decide later you wait to block the current context until one of those pipes complete, you can pull it back into foreground (while maintaining the automatic population of streams/values) by calling "waitToFinish" on the BackgroundTaskInfo.


	def waitToFinish(self, timeout=None, pollInterval=.1):

		'''

			waitToFinish - Wait (Block current thread), optionally with a timeout, until background task completes.



			@param timeout <None/float> - None to wait forever, otherwise max number of seconds to wait

			@param pollInterval <float> - Seconds between each poll. Keep high if interactivity is not important, low if it is.



			@return - None if process did not complete (and timeout occured), otherwise the return code of the process is returned.

		'''


So, to continue the example above:


	pipe1Info = pipe1.runInBackground()


	....hard work...

	sys.stdout.write('Current output: ' + pipe1Info.stdoutData.decode('utf-8'))

	.... more hard work...



	returnCode = pipe1Info.waitToFinish()



Constants
---------

DEFAULT_POLL_INTERVAL = .05 *Number of seconds as default for polling interval*

SUBPROCESS2_DEFAULT_TERMINATE_TO_KILL_SECONDS = 1.5 *Default number of seconds between SIGTERM and SIGKILL for Popen.waitOrTerminate method*

SUBPROCESS2_PROCESS_COMPLETED  = 0 *Mask value for noting that process completed by itself*
SUBPROCESS2_PROCESS_TERMINATED = 1 *Mask value for noting that process was sent SIGTERM*
SUBPROCESS2_PROCESS_KILLED     = 2 *Mask value for noting that process was sent SIGKILL*




Compatability
-------------

It is both python2 and python3 compatable. It has been tested under python 2.7 and 3.4.


Tests / Examples
----------------

Tests are written using the `GoodTests <https://github.com/kata198/GoodTests>`_ framework. They are found in the "tests" directory. Use runTests.py to download GoodTests and run the test suite, after installing subprocess2.

