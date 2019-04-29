#!/usr/bin/python3

# simple XML tags remover for unified input for diff.py

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

# pomocnicza funkcja do konwertowania encji
# obsługujemy tu tylko 5 predefiniowanych w XML
def entitiesToChars(txt):
	entities = [ ['&lt;','<'], ['&gt;','>'], ['&quot;','"'], ['&apos;',"'"], ['&amp;','&'] ]
	for entity in entities:
		txt = txt.replace(entity[0], entity[1])
	return txt

def charsToEntities(txt, full=False):
	entities  = [ ['&amp;','&'] ]
	entities += [ ['&lt;','<'], ['&gt;','>'] ]
	if full:
		entities += [ ['&quot;','"'], ['&apos;',"'"] ]
	for entity in entities:
		txt = txt.replace(entity[1], entity[0])
	return txt

for l in f:
	l = re.sub('<img.*?src="(.*?)".*?>', '\\1', l)
	l = re.sub('<m>(.*?)</m>', '$\\1$', l)
	l = re.sub('</dt><dd>', ' -- ', l)
	l = re.sub('<!--(.*?)-->', '%\\1', l)

	l = re.sub('<.*?>', '', l)
	l = entitiesToChars(l)

	l = re.sub('[  \t]+', ' ', l)
	l = re.sub('^ ', '', l)
	l = re.sub(' \n', '\n', l)
	if l != '\n':
		print(l, end="")

