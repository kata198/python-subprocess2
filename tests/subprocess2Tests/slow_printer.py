#!/usr/bin/env python

import time
import sys

# 0-2 seconds, NOTHING
# 2-5 seconds, 
#	stdout => Hello World\n
#   stderr => NOTHING
# 5-8 seconds,
#	stdout => Hello World\nCheese\n
#   stderr => Goodbye<space>
# 8-10 seconds
#   stdout => Hello World\nCheese\n
#   stderr => Goodbye Cruel World
# 10-11 seconds
#   stdout => Hello World\nCheese\n
#   stderr => Goodbye Cruel World\n
# exit 4

if __name__ == '__main__':
	time.sleep(2)
	sys.stdout.write('Hello World\n')
	sys.stdout.flush()
	time.sleep(3)
	sys.stderr.write('Goodbye ')
	sys.stderr.flush()
	sys.stdout.write('Cheese\n')
	sys.stdout.flush()
	time.sleep(3)
	sys.stderr.write('Cruel World')
	sys.stderr.flush()
	time.sleep(2)
	sys.stderr.write('\n')
	sys.stderr.flush()
	time.sleep(.1)
	sys.exit(4)
