#!/usr/bin/python3

# generate table of content as pdftk bookmarks for pdfs generated from xhtml files

# script dependencies:
#  - python3


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

import xml.etree.ElementTree as xmlParser
import re, sys

if len(sys.argv) != 3:
	print("USAGE:", sys.argv[0], "xhtmlFile xmlFile", file=sys.stderr)
	print("", file=sys.stderr)
	print("generate table of content as pdftk bookmarks for pdfs generated from xhtml files", file=sys.stderr)
	print(" xhtmlFile - source XHTML file for pdf (with hierarchy by <h2/> -- <h5/> tags)", file=sys.stderr)
	print(" xmlFile   - xml output from `pdftohtml -xml` command)", file=sys.stderr)
	print("", file=sys.stderr)
	print("USAGE EXAMPLE:", file=sys.stderr)
	print("  wkhtmltopdf $XML $TMP1", file=sys.stderr)
	print("  pdftk $TMP1 dump_data > $TMP2", file=sys.stderr)
	print("  pdftohtml -xml -stdout $TMP1 | python3 toc.py $XML - >> $TMP2", file=sys.stderr)
	print("  pdftk $TMP1 update_info $TMP2 output $PDF", file=sys.stderr)
	exit(1)

if sys.argv[1] == '-' and sys.argv[2] == '-':
	print("Can't use stdin for both file", file=sys.stderr)
	exit(1)

xhtmlFile = sys.stdin
if sys.argv[1] != '-':
	xhtmlFile = open(sys.argv[1], "r")

xmlFile = sys.stdin
if sys.argv[2] != '-':
	xmlFile = open(sys.argv[2], "r")


# get TOC from xhtml file

xml = xmlParser.ElementTree()
rootNode = xml.parse( xhtmlFile )
toc = []

def getTitle(element):
	for e in element:
		if e.tag.split('}')[1] in ['h2', 'h3', 'h4', 'h5']:
			return e.text

def tableOfContents(element, level):
	title = getTitle(element)
	if title:
		toc.append([title, level])
		level += 1
	
	for e in element:
		tableOfContents(e, level)

tableOfContents(rootNode, 1)


# get pages numbers based on xml file

xml = xmlParser.ElementTree()
rootNode = xml.parse( xmlFile )

pages = {}
fonts = []
xmlTagRegex = re.compile('<.*?>')
spacesRegex = re.compile('[ \t\n]+')

for p in rootNode:
	if p.tag == 'page':
		pn = p.attrib['number']
		
		# find font used for titles
		for e in p:
			if e.tag == 'fontspec' and e.attrib['color'] == '#010101':
				fonts.append(e.attrib['id'])
		
		# join all titles elements on single line
		ptiles = {}
		for e in p:
			if e.tag == 'text' and e.attrib['font'] in fonts:
				line = e.attrib['top']
				# get full tag, because text can be inside child tags
				txt = xmlParser.tostring(e, encoding="unicode")
				# normalise whitespaces
				txt = spacesRegex.sub(' ', txt)
				# strip before remove xml to protect potential spaces at begin/end title element
				txt = txt.strip()
				# remove xml tags
				txt = xmlTagRegex.sub('', txt)
				# concat all title element on line
				ptiles[line] = ptiles.get(line, "") + txt
		
		# add all (joined) titles from actual page to `pages` dict
		for l in ptiles:
			title = ptiles[l]
			if title in pages:
				pages[title].append(pn)
			else:
				pages[title] = [ pn ]


# add page numbers to TOC

for e in toc:
	title = e[0]
	try:
		pn = pages[title].pop(0)
	except KeyError:
		print(pages, file=sys.stderr)
		raise BaseException("Can't find page number for: " + title)
	e.append(pn)


# generate bookmarks

for e in toc:
	print("BookmarkBegin")
	print("BookmarkTitle: " + e[0].encode('ascii', 'xmlcharrefreplace').decode())
	print("BookmarkLevel: " + str( e[1] ))
	print("BookmarkPageNumber: " + e[2])
