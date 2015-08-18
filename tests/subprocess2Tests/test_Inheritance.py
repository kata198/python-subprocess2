#!/usr/bin/env GoodTests.py


import subprocess

import subprocess2


class TestInheritance(object):
    '''
        A general test
    '''


    def test_moduleInherited(self):
        assert subprocess.Popen == subprocess2.Popen , 'Did not inherit Popen'
        assert getattr(subprocess.Popen, 'waitUpTo', False) is not False, 'Did not extend Popen module'


if __name__ == '__main__':
    subprocess.Popen('GoodTests.py "%s"' %(sys.argv[0],), shell=True).wait()
