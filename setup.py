#!/usr/bin/env python

from setuptools import setup

with open('README.rst', 'r') as f:
    long_description = f.read()

if __name__ == '__main__':

    setup(name='python-subprocess2',
            version='0.1.1',
            packages=['subprocess2'],
            author='Tim Savannah',
            author_email='kata198@gmail.com',
            maintainer='Tim Savannah',
            url='https://github.com/kata198/python-subprocess2',
            maintainer_email='kata198@gmail.com',
            description='Extensions to the upstream python subprocess module',
            long_description=long_description,
            license='LGPLv3',
            keywords=['python', 'subprocess', 'Popen', 'pipe', 'wait', 'timeout', 'terminate', 'kill', 'sigterm', 'sigkill', 'process', 'management', 'waitUpTo', 'waitOrTerminate'],
            classifiers=['Development Status :: 5 - Production/Stable',
                         'Programming Language :: Python',
                         'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                          'Programming Language :: Python :: 2',
                          'Programming Language :: Python :: 2.7',
                          'Programming Language :: Python :: 3',
                          'Programming Language :: Python :: 3.4',
                          'Operating System :: POSIX',
                          'Operating System :: POSIX :: Linux',
                          'Operating System :: Unix',
                          'Operating System :: Microsoft :: Windows',
                          'Topic :: System',
            ]
    )



#vim: set ts=4 sw=4 expandtab
