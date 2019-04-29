#!/usr/bin/python3

# compare sections of two files

# Copyright (c) 2019 Robert Ryszard Paciorek <rrp@opcode.eu.org>
# 
# MIT License
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys, os, re, tempfile

# check args
if len(sys.argv) != 3:
	print("USAGE:", sys.argv[0], " fileA fileB", file=sys.stderr)
	print("compare all BEGIN/END block from fileA to corresponding block in fileB", file=sys.stderr)
	exit(1)

# TODO: should be set from command line options:
openBlockRegex = '^(.*?) BEGIN: (.*)\n'
endBlockRepl   = '\\1 END: \\2\n'  # re.sub() replacment string used with openBlockRegex to build blockEnd line
nameBlockRepl  = '\\2'  # re.sub() replacment string used with openBlockRegex to build blockId


# prepare date for diff, and execute diff command
def doSync(linesA, linesB, syncStart, syncStop, bOffset, tag):
	tmpA = tempfile.NamedTemporaryFile(mode="w", dir="/dev/shm")
	tmpA.file.write(''.join( linesA[syncStart:syncStop+1] ))
	tmpA.file.close()
	tmpB = tempfile.NamedTemporaryFile(mode="w", dir="/dev/shm")
	tmpB.file.write(''.join(linesB))
	tmpB.file.close()
	
	# diff command
	cmd = "diff -u " + tmpA.name + " " + tmpB.name
	# fix line numbers in diff with awk script
	cmd = cmd + """ | awk -F'[ ,+-]*' '
		NR==3 {
			printf( \
				"@@ -%d,%d +%d,%d @@ """ + tag + """\\n", \
				$2+""" + str(syncStart) + """, $3, \
				$4+""" + str(bOffset) + """, $5 \
			)
		}
		NR>3 {
			print $0
		}
	'"""
	# exec diff command
	os.system(cmd)

# read file from start tag to end tag
def readFromTo(src, start, end, dst):
	inBlock = False
	blockStartLine = 0
	while True:
		ll = src.readline()
		if ll == start:
			inBlock = True
		if inBlock:
			dst.append(ll)
		else:
			blockStartLine += 1
		if not ll or ll == end:
			return blockStartLine


# init - open files, set variables, etc
fileA, fileB =open(sys.argv[1], "r"), open(sys.argv[2], "r")
linesA, linesB = [], []
syncStart, syncStop = 0, 0
blockId, blockEnd = None, None
blockRegEx = re.compile(openBlockRegex)

# print diff header (info abiut compared files)
print("--- " + sys.argv[1])
print("+++ " + sys.argv[2])
sys.stdout.flush()

# main loop -- read first file
while True:
	lA = fileA.readline()
	
	# check EOF
	if not lA:
		break
	
	# check begin / end points
	if blockRegEx.match(lA):
		blockEnd  = blockRegEx.sub(endBlockRepl, lA)
		blockId   = blockRegEx.sub(nameBlockRepl, lA)
		syncStart = len(linesA)
	if lA == blockEnd:
		syncStop  = len(linesA)
	
	# append lines from A file
	linesA.append(lA)
	
	# search lines from B file
	if syncStop:
		fileB.seek(0)
		linesB.clear()
		bOffset = readFromTo(fileB, linesA[syncStart], linesA[syncStop], linesB)
		doSync(linesA, linesB, syncStart, syncStop, bOffset, blockId)
		syncStop = False
