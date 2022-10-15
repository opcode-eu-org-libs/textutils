#!/bin/bash

# convert (print) xhtml file into pdf file, use wkhtmltopdf to create pdf and
# pdftk + pdftohtml + toc2pdf.py to add table of content as pdf bookmarks

# script dependencies:
#  - wkhtmltopdf (wkhtmltopdf package)
#  - pdftk       (pdftk package)
#  - pdftohtml   (poppler-utils package)
#  - toc2pdf.py  (from this repo, should be place in the same directory as this script)


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

# exit on errors
set -e

# get this script dir path
SRCDIR=$(dirname $(realpath $0))

# check args
if [ $# -ne 1 -a $# -ne 2 ]; then
	echo "USAGE: $0 input.xhtml [output.pdf]"
	exit 1
fi

# get input and output filepaths
input=$1
if [ $# -eq 2 ]; then
	output=$2
else
	output=${input%.*}.pdf
fi

# create PDF
wkhtmltopdf --enable-local-file-access -s A4 -B 20 -T 20 -L 15 -R 20 $input $output

# prepare TOC as PDF bookmarks
TMP1=`mktemp -t 'XXXXXXXXXXX.info'`
pdftk $output dump_data > $TMP1
pdftohtml -xml -i -stdout $output | python3 $SRCDIR/toc2pdf.py $input - >> $TMP1
TMP2=`mktemp -t 'XXXXXXXXXXX.pdf'`

# add PDF bookmarks
pdftk $output update_info $TMP1 output $TMP2

# move temporary file to output file path and fix permissions
mv $TMP2 $output
chmod `umask -S | tr -d 'x'` $output

# cleanup
rm $TMP1
