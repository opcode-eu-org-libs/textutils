#!/usr/bin/python3

# simple TeX tags remover for unified input for diff.py

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

import sys, re

if len(sys.argv) == 2:
	f = open(sys.argv[1])
else:
	f = sys.stdin


for l in f:
	l, n = re.subn('^([^$]*)(\$[^$]*)\\\\([^$]*\$)', '\\1\\2@@%%@@\\3', l)
	while n:
		l, n = re.subn('^(([^$]*\$[^$]*\$[^$]*)*)(\$[^$]*)\\\\([^$]*\$)', '\\1\\3@@%%@@\\4', l)
	l = re.sub('\\\\begin(\{.*?\})*', '', l)
	l = re.sub('\\\\end\{.*?\}', '', l)
	l = re.sub('\\\\label\{.*?\}', '', l)
	
	l = re.sub('\\\\[a-z]*section\{(.*?)\}', '\\1', l)
	l = re.sub('\\\\lstinline\{(.*?)\}', '\\1', l)
	l = re.sub('\\\\lstinline@(.*?)@', '\\1', l)
	l = re.sub('\\\\text..\{(.*?)\}', '\\1', l)
	l = re.sub('\{\\\\it (.*?)\}', '\\1', l)
	l = re.sub('\{\\\\bf (.*?)\}', '\\1', l)
	l = re.sub('([^\\\\])~', '\\1 ', l)
	
	l = re.sub('\\\\.space\{.*?\}', '', l)
	l = re.sub('\\\\itemsep\{.*?\}', '', l)
	l = re.sub(',,', '', l)
	l = re.sub("''", '', l)

	l = re.sub('\\\\[\\\\a-zA-Z]+(\[.*?\])*', '', l)
	l = re.sub('@@%%@@', '\\\\', l)
	
	l = re.sub('[  \t]+', ' ', l)
	l = re.sub('^ ', '', l)
	l = re.sub(' \n', '\n', l)
	if l != '\n':
		print(l, end="")

