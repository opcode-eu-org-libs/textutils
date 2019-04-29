#!/bin/bash

# script to add md5sum and source filename to pdf for printing

# script dependencies:
#  - md5sum  (coreutils package)
#  - pdfinfo (poppler-utils package)
#  - gs      (ghostscript package)
#  - pdftk   (pdftk package)
#
#  NimbusMonoPS-Bold font are included in ghostscript dependencies (libgs9-common package)


# Copyright (c) 2014-2019 Robert Ryszard Paciorek <rrp@opcode.eu.org>
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


if [ $# -ne 1 -a $# -ne 2 ]; then
	echo "USAGE: $0 file.pdf [up]"
	echo ""
	echo "Script create file__MD5__.pdf with added overlay information about md5sum of file.pdf"
	echo "  when call without \"up\" argument md5sum will be added on page bottom"
	echo "  when optional second argument \"up\" is used md5sum will be added on page top"
	exit 1
fi

INPUT="$1"
UP=false
[ "$2" = "up" ] && UP=true

# get pdf info
MD5=`md5sum "${INPUT}" | cut -f1 -d' '`
PAGE_SIZE=`pdfinfo "${INPUT}" | grep '^Page size:'`
PAGE_SIZE_X=`echo $PAGE_SIZE | awk '{print $3 * 10}'`
PAGE_SIZE_Y=`echo $PAGE_SIZE | awk '{print $5 * 10}'`
TEXT_OFFSET_X="32"
TEXT_OFFSET_Y="32"
$UP && TEXT_OFFSET_Y=$[ ${PAGE_SIZE_Y}/10 - 48 ]

# prepare stamp file
STAMPFILE=`mktemp`
gs -o ${STAMPFILE} -sDEVICE=pdfwrite -g${PAGE_SIZE_X}x${PAGE_SIZE_Y} \
	-c "/NimbusMonoPS-Bold findfont 8 scalefont setfont" \
	-c "0 0 0 .48 setcmykcolor" -c "${TEXT_OFFSET_X} ${TEXT_OFFSET_Y} moveto" \
	-c "(MD5: ${MD5}  FILE: ${INPUT}) show" -c "showpage"

# join input pdf and stamp file
pdftk "${INPUT}" stamp ${STAMPFILE} output "${INPUT%.pdf}__MD5__.pdf"

# cleanup temporary file
rm -f ${STAMPFILE}
