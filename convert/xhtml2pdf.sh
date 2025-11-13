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
input="$1"
if [ $# -eq 2 ]; then
	output="$2"
else
	output="${input%.*}.pdf"
fi

# create PDF
TMP_XHTML=$(realpath $(mktemp -p "`dirname "$input"`" -t 'XXXXXXXXXXX.xhtml')) # need be in the same directory as $input (due to relative links in html)
TMP_PDF_OUT1=`mktemp -t 'XXXXXXXXXXX.pdf'`
sed -e 's|</head>|<style> @page { margin: 0.3in 0.35in 0.3in 0.15in; size: 8.3in 11.7in; } h1, h2, h3, h4, h5, h6 { color: #020202; } </style></head>|' "$input" > "$TMP_XHTML"
# backward compatibility: toc2pdf.py need titles color #010101 (this was title color in wkhtmltopdf output) ... chromium generate #010101 in pdf output from #020202 in html input
chromium --headless --print-to-pdf="$TMP_PDF_OUT1" --no-pdf-header-footer -print-to-pdf-no-header "$TMP_XHTML"

# prepare TOC as PDF bookmarks
TMP_TOC_DATA=`mktemp -t 'XXXXXXXXXXX.info'`
pdftk $TMP_PDF_OUT1 dump_data > $TMP_TOC_DATA
pdftohtml -xml -i -stdout $TMP_PDF_OUT1 | python3 $SRCDIR/toc2pdf.py "$input" - >> $TMP_TOC_DATA

# add PDF bookmarks
pdftk "$TMP_PDF_OUT1" update_info $TMP_TOC_DATA output $output

# fix permissions
chmod `umask -S | tr -d 'x'` "$output"

# cleanup
rm "$TMP_XHTML" $TMP_PDF_OUT1 $TMP_TOC_DATA
