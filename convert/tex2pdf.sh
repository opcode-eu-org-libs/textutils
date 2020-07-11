#!/bin/bash

# build tex file (with lualatex) until no changes in .out and .aux file

# script dependencies:
#  - md5sum  (coreutils package)
#  - lualatex (texlive-latex-base texlive-luatex texlive-latex-recommended packages)


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

set -e

buildTex() {
	inputPath=$1; inputName=$2; shift 2
	md5sum "$inputName.aux" "$inputName.out" > "$inputName.md5" 2> /dev/null || true
	lualatex --halt-on-error  "$@" "$inputPath/$inputName.tex"
}

# args ...
if [ $# -lt 1 ]; then
	echo "USAGE: $0 fileName.tex [extra args for lualatex, eg. -shell-escape]" > /dev/stderr
	exit 1
fi

inputPath=`dirname  $1`
inputName=`basename $1 .tex`
shift

# first build
buildTex "$inputPath" "$inputName" "$@"; i=1

# rebuild until build changes .aux or .out files
while ! md5sum -c "$inputName.md5" >& /dev/null; do
	buildTex "$inputPath" "$inputName" "$@"
	let i++
	if [ $i -gt 4 ]; then
		echo "exceeded maximum number of lualatex iteration ... break" > /dev/stderr
		exit 2
	fi
done;

echo "we need $i iteration to build $inputName"
exit 0
