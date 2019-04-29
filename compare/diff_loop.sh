#!/bin/bash

# run unxml.py, untex.py and diff.py on each input files update

# script dependencies:
#  - inotifywait  (inotify-tools package)
#  - diff.py, untex.py, unxml.py (from this repo, should be place in the same directory as this script)


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

toolsDir=$(dirname $(realpath $0))

toText() {
	name=`basename "$1"`
	nn=${name%.*}
	case ${name#$nn} in
		".xhtml"|".xml"|".html")
			$toolsDir/unxml.py "$1"
			;;
		".tex")
			$toolsDir/untex.py "$1"
			;;
		*)
			echo "$1 don't have supported extension" > /dev/stderr
			exit 1
			;;
	esac
}

doCompare() {
	toText "$1" > /tmp/`basename "$1"`;
	toText "$2" > /tmp/`basename "$2"`;
	$toolsDir/diff.py /tmp/`basename "$1"` /tmp/`basename "$2"` > /tmp/XX.diff;
	echo "/tmp/XX.diff updated on `date --utc +'%F %T %Z'`"
}

doCompare "$1" "$2"
while inotifywait "$1" "$2"; do
	doCompare "$1" "$2"
done
