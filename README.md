# python-subprocess2

Extensions on the python subprocess module. Importing subprocess2 will extend the global "subprocess" module (only additions, no modifications, so it's safe). 

You can also import and use subprocess2 instead of the subprocess module. Doing a global extension allows your application or library to utilize the extensions without requiring modification of other codebases. In example, if you have a library that is opening a pipe and passing it to your application, it does not need to be modified for you to use the additional Popen methods on the object you received.


Simply installing the subprocess2 module does not do anything to the parent subprocess module, until it has been imported, and then only additions are made.



PyDoc Reference
---------------

PyDoc Reference for extended subprocess modules can be found at: http://htmlpreview.github.io/?https://github.com/kata198/python-subprocess2/blob/master/doc/subprocess2.html



Popen
=====

Additions to Popen class:


waitUpTo
--------

This method adds the ability to specify a timeout when waiting for a subprocess to complete.


	Popen.waitUpTo (timeoutSeconds, pollInterval) - Wait up to a certain number of seconds for the process to end.
	
		@param timeoutSeconds <float> - Number of seconds to wait

		@param pollInterval <float> (default .05) - Number of seconds in between each poll
	
		@return - Returncode of application, or None if did not terminate.
	
	

waitOrTerminate
---------------

This method allows specifying a timeout, like waitUpTo, but will also handle terminating or killing the application if it exceeds the timeout (see documentation below).


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


Constants
---------

DEFAULT\_POLL\_INTERVAL = .05 *Number of seconds as default for polling interval*

SUBPROCESS2\_DEFAULT\_TERMINATE\_TO\_KILL\_SECONDS = 1.5 *Default number of seconds between SIGTERM and SIGKILL for Popen.waitOrTerminate method*

SUBPROCESS2\_PROCESS\_COMPLETED  = 0 *Mask value for noting that process completed by itself*
SUBPROCESS2\_PROCESS\_TERMINATED = 1 *Mask value for noting that process was sent SIGTERM*
SUBPROCESS2\_PROCESS\_KILLED     = 2 *Mask value for noting that process was sent SIGKILL*


Compatability
-------------

It is both python2 and python3 compatable. It has been tested under python 2.7 and 3.4.

Tests / Examples
----------------

Tests are written using the GoodTests ( <https://github.com/kata198/GoodTests> ) framework. They are found in the "tests" directory. Use runTests.py to download GoodTests and run the test suite, after installing subprocess2.
