'''
  simple.py - Simple subprocess commands
   
  Copyright (c) 2016 Timothy Savannah LGPLv2 All rights reserved. See LICENSE file for more details.

    
'''

# vim: ts=4 sw=4 expandtab :

import select
import sys
import time

import subprocess

__all__ = ('Simple', 'SimpleCommandFailure')

class Simple(object):
    '''
        Simple - Simple and quick commands to run a subprocess and get the results.

        Static Methods:

            runGetOutput - Simply runs a command and returns the program's output. Optionally raises SimpleCommandFailure on failure. @see #runGetOutput for more details.

            runGetResults - Runs a command and based on paramaters returns a dict containing: returnCode, stdout, stderr. @see #runGetResults for more details.
    '''

    @staticmethod
    def runGetResults(cmd, stdout=True, stderr=True, encoding=sys.getdefaultencoding()):
        '''
            runGetResults - Simple method to run a command and return the results of the execution as a dict.

            @param cmd <str/list> - String of command and arguments, or list of command and arguments

                If cmd is a string, the command will be executed as if ran exactly as written in a shell. This mode supports shell-isms like '&&' and '|'
                If cmd is a list, the first element will be the executable, and further elements are arguments that will be passed to that executable.

            @param stdout <True/False> - Default True, Whether to gather and include program's stdout data in results.

                If False, that data the program prints to stdout will just be output to the current tty and not recorded.
                If True, it will NOT be output to the tty, and will be recorded under the key "stdout" in the return dict.

            @param stderr <True/False or "stdout"/subprocess.STDOUT> - Default True, Whether to gather and include program's stderr data in results, or to combine with "stdout" data.

                If False, the data the program prints to stderr will just be output to the current tty and not recorded
                If True, it will NOT be output to the tty, and will be recorded under the key "stderr" in the return dict.
                If "stdout" or subprocess.STDOUT - stderr data will be blended with stdout data. This requires that stdout=True.


            @param encoding <None/str> - Default sys.getdefaultencoding(), the program's output will automatically be decoded using the provided codec (e.x. "utf-8" or "ascii").

                If None or False-ish, data will not be decoded (i.e. in python3 will be "bytes" type)

                If unsure, leave this as it's default value, or provide "utf-8"

            @return <dict> - Dict of results. Has following keys:

                'returnCode' - <int> - Always present, included the integer return-code from the command.
                'stdout'       <unciode/str/bytes (depending on #encoding)> - Present if stdout=True, contains data output by program to stdout, or stdout+stderr if stderr param is "stdout"/subprocess.STDOUT
                'stderr'       <unicode/str/bytes (depending on #encoding)> - Present if stderr=True, contains data output by program to stderr.


            @raises - SimpleCommandFailure if it cannot launch the given command, for reasons such as: cannot find the executable, or no permission to execute, etc
        '''
   
        if stderr in ('stdout', subprocess.STDOUT):
            stderr = subprocess.STDOUT
        elif stderr == True or stderr == subprocess.PIPE:
            stderr = subprocess.PIPE
        else:
            stderr = None

        if stdout == True or stdout == subprocess.STDOUT:
            stdout = subprocess.PIPE
        else:
            stdout = None
            if stderr == subprocess.PIPE:
                raise ValueError('Cannot redirect stderr to stdout if stdout is not captured.')

        if issubclass(cmd.__class__, (list, tuple)):
            shell = False
        else:
            shell = True

        try:
            pipe = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, shell=shell)
        except Exception as e:
            try:
                if shell is True:
                    cmdStr = ' '.join(cmd)
                else:
                    cmdStr = cmd
            except:
                cmdStr = repr(cmd)

            raise SimpleCommandFailure('Failed to execute "%s": %s' %(cmdStr, str(e)), returnCode=255)


        streams = []
        fileNoToKey = {}
        ret = {}
        if stdout == subprocess.PIPE:
            streams.append(pipe.stdout)
            fileNoToKey[pipe.stdout.fileno()] = 'stdout'
            ret['stdout'] = []
        if stderr == subprocess.PIPE:
            streams.append(pipe.stderr)
            fileNoToKey[pipe.stderr.fileno()] = 'stderr'
            ret['stderr'] = []

        returnCode = None


        time.sleep(.02)
        while returnCode is None or streams:
            returnCode = pipe.poll()

            while True:
                (readyToRead, junk1, junk2) = select.select(streams, [], [], .005)
                if not readyToRead:
                    # Don't strangle CPU
                    time.sleep(.01)
                    break

                for readyStream in readyToRead:

                    retKey = fileNoToKey[readyStream.fileno()]
                    curRead = readyStream.read()
                    if curRead == '':
                        streams.remove(readyStream)
                        continue
                    ret[retKey].append(curRead)


        for key in list(ret.keys()):
            ret[key] = b''.join(ret[key])
            if encoding:
                ret[key] = ret[key].decode(encoding)

        ret['returnCode'] = returnCode
        
        return ret

    @staticmethod
    def runGetOutput(cmd, raiseOnFailure=False, encoding=sys.getdefaultencoding()):
        '''
            runGetOutput - Simply runs a command and returns the output as a string. Use #runGetResults if you need something more complex.

            @param cmd <str/list> - String of command and arguments, or list of command and arguments

                If cmd is a string, the command will be executed as if ran exactly as written in a shell. This mode supports shell-isms like '&&' and '|'
                If cmd is a list, the first element will be the executable, and further elements are arguments that will be passed to that executable.


            @param raiseOnFailure <True/False> - Default False, if True a non-zero return from the command (failure) will raise a SimpleCommandFailure, which contains all gathered output and return code. @see #SimpleCommandFailure

            
            @param encoding <None/str> - Default sys.getdefaultencoding(), the program's output will automatically be decoded using the provided codec (e.x. "utf-8" or "ascii").

                If None or False-ish, data will not be decoded (i.e. in python3 will be "bytes" type)

                If unsure, leave this as it's default value, or provide "utf-8"


            @return <str> - String of data output by the executed program. This combines stdout and stderr into one string. If you need them separate, use #runGetResults

            @raises SimpleCommandFailure - 

                * If command cannot be executed (like program not found, insufficient permissions, etc)

                * If #raiseOnFailure is set to True, and the program returns non-zero

        '''


        
        results = Simple.runGetResults(cmd, stdout=True, stderr=subprocess.STDOUT, encoding=encoding)
        if raiseOnFailure is True and results['returnCode'] != 0:
            try:
                if issubclass(cmd.__class__, (list, tuple)):
                    cmdStr = ' '.join(cmd)
                else:
                    cmdStr = cmd
            except:
                cmdStr = repr(cmd)
                
            failMsg = "Command '%s' failed with returnCode=%d" %(cmdStr, results['returnCode'])
            raise SimpleCommandFailure(failMsg, results['returnCode'], results.get('stdout', None), results.get('stderr', None))
            

        return results['stdout']


class SimpleCommandFailure(Exception):
    '''
        SimpleCommandFailure - An exception representing a failure in execution of a command using the subprocess2.Simple interfaces.

        Contains the following properties:

            * msg <str> - The exception message itself

            * returnCode <int> - The return code of the execution

            * stdout <None/str> - Any collected stdout data, or "None" if none was collected.

            * stderr <None/str> - Any collected stderr data, or "None" if none was collected.

    '''


    def __init__(self, msg, returnCode, stdout=None, stderr=None):
        self.returnCode = returnCode
        self.stdout = stdout
        self.stderr = stderr
        Exception.__init__(self, msg)
        self.msg = msg


Simple.SimpleCommandFailure = SimpleCommandFailure
