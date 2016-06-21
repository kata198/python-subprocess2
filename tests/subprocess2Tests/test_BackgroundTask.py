#!/usr/bin/env GoodTests.py

import os
import sys
import subprocess
import time

import subprocess2


class TestBackgroundTask(object):
    '''
        Tests some background task stuff
    '''

    def setup_class(self):
        self.dirName = os.path.dirname(__file__)
        self.slowPrinterPath = "%s/slow_printer.py" %(self.dirName, )
        if not os.path.exists(self.slowPrinterPath):
            sys.stderr.write('ERROR! CANNOT FIND slow_printer.py in test directory. Test will fail.\n')


    def test_runInBackground(self):
        '''
            test_runInBackground - Tests runInBackground against the following script:
# 0-2 seconds, NOTHING
# 2-5 seconds, 
#    stdout => Hello World\n
#   stderr => NOTHING
# 5-8 seconds,
#    stdout => Hello World\nCheese\n
#   stderr => Goodbye<space>
# 8-10 seconds
#   stdout => Hello World\nCheese\n
#   stderr => Goodbye Cruel World
# 10-11 seconds
#   stdout => Hello World\nCheese\n
#   stderr => Goodbye Cruel World\n
# exit 4
        '''
        pipe = subprocess.Popen([self.slowPrinterPath], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        bgData = pipe.runInBackground(.1)
        time.sleep(1)
        assert bgData.isFinished is False , 'Already finished, should still be running'
        assert bgData['isFinished'] is False , 'Dict interface did not work'
        assert bgData.returnCode is None , 'Return code given, should still be running'

        assert not bgData.stdoutData , 'No data should be populated on stdout, got %s' %(bgData.stdoutData.decode('utf-8'),)
        assert not bgData.stderrData , 'No data should be populated on stderr, got %s' %(bgData.stderrData.decode('utf-8'),)

        time.sleep(2.5)
        # 3ish seconds in
        assert bgData.timeElapsed < 4 and bgData.timeElapsed > 2 , 'Time elapsed is off, expected to be about 3 seconds, got %f' %(float(bgData.timeElapsed),)
        assert bgData.stdoutData.decode('utf-8') == 'Hello World\n', 'Data did not match script at 3 seconds, was: %s' %(repr(bgData.stdoutData.decode('utf-8')))
        assert not bgData.stderrData.decode('utf-8') , 'Data did not match script at 3 seconds'

        time.sleep(3)
        # 6 seconds in
        assert bgData.timeElapsed < 7 and bgData.timeElapsed > 5 , 'Time elapsed is off, expected to be about 6 seconds, got %f' %(float(bgData.timeElapsed),)
        assert bgData.stdoutData.decode('utf-8') == 'Hello World\nCheese\n', 'Data did not match at 6 seconds'
        assert bgData.stderrData.decode('utf-8') == 'Goodbye ' , 'Non-newlined data was not picked up on stderr at 6 seconds'
        time.sleep(3.5)

        # 9.5 seconds
        assert bgData.timeElapsed < 10.5 and bgData.timeElapsed > 8.5 , 'Time elapsed is off, expected to be about 9.5 seconds, got %f' %(float(bgData.timeElapsed),)
        assert bgData.stdoutData.decode('utf-8') == 'Hello World\nCheese\n', 'Data did not match at 9.5 seconds'
        assert bgData.stderrData.decode('utf-8') == 'Goodbye Cruel World' , 'Non-newlined data was not picked up on stderr at 9.5 seconds'

        time.sleep(4)
        # 13.5 seconds
        assert bgData.isFinished is True , 'Expected app to be finished at 13.5 seconds'
        assert bgData.returnCode == 4 , 'Expected return code from app to be 4, got %s' %(str(bgData.returnCode),)

    def test_encodings(self):
        if bytes == str:
            encodedType = str
            decodedType = unicode
        else:
            encodedType = bytes
            decodedType = str

        pipe = subprocess.Popen([self.slowPrinterPath], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        bgData = pipe.runInBackground(.1)
        time.sleep(3)

        assert type(bgData.stdoutData) == encodedType , 'Expected no provided encoding to be encoded type (%s), got %s' %(encodedType.__name__, type(bgData.stdoutData).__name__)
        pipe.terminate()
        try:
            os.kill(pipe.pid, 9)
        except:
            pass
        pipe.wait()

        pipe = subprocess.Popen([self.slowPrinterPath], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        bgData = pipe.runInBackground(.1, encoding='utf-8')
        time.sleep(3)

        assert type(bgData.stdoutData) == decodedType , 'Expected data read when encoding="utf-8" to be encoded type (%s), got %s' %(decodedType.__name__, type(bgData.stdoutData).__name__)
        pipe.terminate()
        try:
            os.kill(pipe.pid, 9)
        except:
            pass
        pipe.wait()


if __name__ == '__main__':
    subprocess.Popen('GoodTests.py "%s"' %(sys.argv[0],), shell=True).wait()
