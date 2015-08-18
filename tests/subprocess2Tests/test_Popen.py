#!/usr/bin/env GoodTests.py

import os
import sys
import subprocess
import time

import subprocess2


class TestPopen(object):
    '''
        A general test
    '''

    def setup_class(self):
        self.dirName = os.path.dirname(__file__)
        self.sleeperPath = "%s/sleeper.py" %(self.dirName, )
        if not os.path.exists(self.sleeperPath):
            sys.stderr.write('ERROR! CANNOT FIND sleeper.py in test directory. Test will fail.\n')

    def _getSleeperCommand(self, sleepTime, returnCode=0, sigtermReturnCode=254):
        return [self.sleeperPath, str(sleepTime), str(returnCode), str(sigtermReturnCode)]


    def test_waitUpToSuccess(self):
        '''
            Test Popen.waitUpTo in successful cases.
        '''
        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(1.5, 0), shell=False)
        returnCode = pipe.waitUpTo(2)
        end = time.time()

        assert returnCode == 0 , 'waitUpTo did not transfer expected return code 0. Got: %s' %(str(returnCode),)
        assert end - start < 2 , 'waitUpTo took longer than max time.'

        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(.5, 16), shell=False)
        returnCode = pipe.waitUpTo(1)
        end = time.time()

        assert returnCode == 16 , 'waitUpTo did not transfer expected return code 16. Got: %s' %(str(returnCode),)
        assert end - start < 1 , 'waitUpTo took longer than max time.'

    def test_waitUpToFailure(self):
        '''
            Test Popen.waitUpTo in failure cases.
        '''
        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(3, 0), shell=False)
        returnCode = pipe.waitUpTo(1)
        end = time.time()

        assert returnCode is None , 'waitUpTo should have returned None as application should not have completed. Got: %s' %(returnCode,)
        assert end - start < 1.2 , 'waitUpTo took longer than max time.'

    def test_waitOrTerminateSuccess(self):
        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(.25, 1), shell=False)
        ret = pipe.waitOrTerminate(1)
        end = time.time()

        (returnCode, actionTaken) = (ret['returnCode'], ret['actionTaken'])

        assert returnCode is 1, 'waitOrTerminate should have returned 1. Got: %s' %(returnCode,)
        assert end - start < .5 , 'waitOrTerminate took longer than max time.'

        assert actionTaken == subprocess2.SUBPROCESS2_PROCESS_COMPLETED, 'Expected actionTaken mask be blank (COMPLETED)'


    def test_waitOrTerminateFailTerminateOnlyWithKillTimeout(self):
        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(.5, 1, 2), shell=False)
        ret = pipe.waitOrTerminate(.25, terminateToKillSeconds=2)
        end = time.time()

        (returnCode, actionTaken) = (ret['returnCode'], ret['actionTaken'])

        assert actionTaken == subprocess2.SUBPROCESS2_PROCESS_TERMINATED, 'Expected actionTaken mask to contain terminated'

        assert returnCode is 2, 'SIGTERM handler should have returned 2. "1" is non-sigterm return. Got: %s' %(returnCode,)
        assert end - start < .75 , 'waitOrTerminate took longer than max time.'

    def test_waitOrTerminateFailTerminateOnlyWithoutKillTimeout(self):
        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(.5, 1, 2), shell=False)
        ret = pipe.waitOrTerminate(.25, terminateToKillSeconds=None)
        end = time.time()

        (returnCode, actionTaken) = (ret['returnCode'], ret['actionTaken'])

        assert actionTaken == subprocess2.SUBPROCESS2_PROCESS_TERMINATED , 'Expected actionTaken mask to contain terminated'

        assert returnCode is 2, 'SIGTERM handler should have returned 2. "1" is non-sigterm return. Got: %s' %(returnCode,)
        assert end - start < .75 , 'waitOrTerminate took longer than max time.'

    def test_waitOrTerminateFailKillOnly(self):
        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(.5, 1, 2), shell=False)
        ret = pipe.waitOrTerminate(.25, pollInterval=.01, terminateToKillSeconds=0)
        end = time.time()

        (returnCode, actionTaken) = (ret['returnCode'], ret['actionTaken'])

        assert actionTaken == subprocess2.SUBPROCESS2_PROCESS_KILLED , 'Expected actionTaken mask to contain kill'
        assert returnCode is None, 'SIGKILL should have returned None. "1" is non-sigterm return. "2" is sigerm return. Got: %s' %(returnCode,)
        assert end - start < .4, 'waitOrTerminate took longer than max time.'

    def test_waitOrTerminateFailTerminateAndKill(self):
        start = time.time()
        pipe = subprocess.Popen(self._getSleeperCommand(7, 1, 250), shell=False) # 250 is special command to sleeper.py to continue running after sigterm
        ret = pipe.waitOrTerminate(.25, terminateToKillSeconds=2)
        end = time.time()

        (returnCode, actionTaken) = (ret['returnCode'], ret['actionTaken'])

        assert actionTaken == (subprocess2.SUBPROCESS2_PROCESS_TERMINATED | subprocess2.SUBPROCESS2_PROCESS_KILLED) , 'Expected actionTaken mask to contain both term and kill'
        assert returnCode is None, 'SIGKILL should have returned None. "1" is non-sigterm return. "250" is sigerm return. Got: %s' %(returnCode,)
        assert end - start < 2.5, 'waitOrTerminate took longer than max time.'
        assert end - start > 2, 'waitOrTerminate killed to quickly.'


if __name__ == '__main__':
    subprocess.Popen('GoodTests.py "%s"' %(sys.argv[0],), shell=True).wait()
