#!/usr/bin/python3

# convert xml files (used in sources of my webpages) to XHTML:
#  * replace <section> by <div>, because <section> is not XHTML 1.1 element
#  * replace <p> by <div>, because <p> is not logical paragraph -- can't contain <ul>, <ol>, etc
#  * replace <m> with LaTeX equation by <span><math> with MathML equation
#  * insert source code specifierd by <insertSourceCode> and prepare for highlight via CSS
#  * create table of content
#  * add <!DOCTYPE

# script dependencies:
#  - python3
#  - pygments python module (python3-pygments package)
#  - latex2mathml python module (https://github.com/roniemartinez/latex2mathml, instal via `pip3 install latex2mathml`)


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

import re, sys, os
import xml.etree.ElementTree as xmlParser

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

import latex2mathml.converter as MathConv
MathConv.COMMANDS['\\sfrac'] = (2, 'mfrac', {'bevelled': 'true'})

# command line arguments
if len(sys.argv) != 3 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
	print("USAGE:", sys.argv[0], "inputFile outputFile", file=sys.stderr)
	exit(1)

inputFile = sys.stdin
inputPath = os.getcwd() + "/"
if sys.argv[1] != '-':
	inputFile = open(sys.argv[1], "r")
	inputPath = os.path.dirname(os.path.realpath(sys.argv[1])) + "/"

outputFile = sys.stdout
if sys.argv[2] != '-':
	outputFile = open(sys.argv[2], "w")


# regexp for split namespace and tag name
tagSplitRegex = re.compile("[{}]")

# main parsing function
def parseDoc(element, level):
	tag      = tagSplitRegex.split(element.tag)
	tagName  = tag[-1]
	
	if tagName == 'section':
		level = addToTOC(element, level)
		element.tag = "{" + defaultNameSpace + "}" + "div"
		addClass(element, "section")
	elif tagName == 'p':
		element.tag = "{" + defaultNameSpace + "}" + "div"
		addClass(element, "par")
	elif tagName == 'm':
		element.tag = "{" + defaultNameSpace + "}" + "span"
		#addClass(element, "math")
		addMathML(element)
	elif tagName == 'insertSourceCode':
		element.tag = "{" + defaultNameSpace + "}" + "pre"
		addSourceCode(element)
	
	for e in element:
		parseDoc(e, level)


# add value to class list
def addClass(element, value):
	if "class" in element.attrib:
		element.attrib["class"] = value + " " + element.attrib["class"]
	else:
		element.attrib["class"] = value


# convert latex to mathml
def addMathML(element):
	element.attrib['title'] = "LaTeX: " + element.text
	mathML = MathConv.convert(element.text)
	mathML = xmlParser.fromstring(mathML)
	mathML.attrib['xmlns'] = "http://www.w3.org/1998/Math/MathML"
	# reparse to add namespace prefix for mathML childs ...
	mathML = xmlParser.fromstring(xmlParser.tostring(mathML))
	element.text = ""
	element.append(mathML)


# add source code from external file and prepare highlight
def addSourceCode(element, filePath=inputPath, useHighlight=True):
	filename = element.attrib["file"]
	if "type" in element.attrib:
		ext = element.attrib["type"]
	else:
		ext = filename.rsplit(".",1)[1]
	
	if ext == "sh":
		ext = "bash"
	elif ext == "py":
		ext = "python"
	elif ext == "js":
		ext = "javascript"
	
	srcFile = open(filePath + filename)
	srcTxt = srcFile.read()
	srcFile.close()
	
	if useHighlight:
		srcTxt = highlight(srcTxt, get_lexer_by_name(ext), HtmlFormatter(nowrap=True))
	
	if srcTxt[0] != '\n':
		srcTxt = '\n' + srcTxt
	if srcTxt[-1] != '\n':
		srcTxt = srcTxt + '\n'
	
	if useHighlight:
		srcHtml = xmlParser.fromstring("<pre>" + srcTxt + "</pre>")
		tail = element.tail
		element.clear()
		element.text = srcHtml.text
		element.tail = tail
		for ee in srcHtml:
			element.append(ee)
	else:
		element.text = srcTxt
	
	element.attrib.clear()
	element.attrib['class'] = ext + " pygments"


# prepare and generate Table Of Content
toc = {}
notInIdRegex = re.compile("[\"',()/+?]+")
def addToTOC(element, level):
	def getTitleNode(element):
		for e in element:
			if tagSplitRegex.split(e.tag)[-1] in ['h1', 'h2', 'h3', 'h4', 'h5']:
				return e
		return None
	
	title = getTitleNode(element)
	if title != None:
		if 'id' in element.attrib:
			idVal = element.attrib['id']
		else:
			idVal = notInIdRegex.sub('', title.text.replace(" ", "_"))
			element.attrib['id'] = idVal
		if idVal in toc:
			idValTmp = idVal
			i = 0
			while idVal in toc:
				i += 1
				idVal = idValTmp + "_" + str(i)
			element.attrib['id'] = idVal
		toc[idVal] = [title.text, level]
		level += 1
	return level

def createTOC():
	lastLevel = 0
	tocTxt = ""
	for idVal, [title, level] in toc.items():
		while level <= lastLevel:
			tocTxt += lastLevel * ' ' + '</ul></li>\n'
			lastLevel -= 1
		tocTxt += level * ' ' + '<li class="menu' + str(level) + '"><a href="#' + idVal + '">' + title + '</a><ul>\n'
		lastLevel = level
	while 1 <= lastLevel:
		tocTxt += lastLevel * ' ' + '</ul></li>\n'
		lastLevel -= 1
	return re.sub('<ul>[\n\t ]*</ul>', '', tocTxt)

def addTOC(element):
	tocContent = xmlParser.fromstring("<toc>" + createTOC() + "</toc>")
	tocNode = element.find(".//{" + defaultNameSpace + "}ul[@id='toc']")
	tail = tocNode.tail
	tocNode.clear()
	tocNode.text = tocContent.text
	tocNode.tail = tail
	for ee in tocContent:
		tocNode.append(ee)
	tocNode.attrib['id'] = 'toc'


# open and parse xml file
defaultNameSpace = 'http://www.w3.org/1999/xhtml'
xmlParser.register_namespace('', defaultNameSpace)
xmlParser.register_namespace('svg', 'http://www.w3.org/2000/svg')
xmlParser.register_namespace('m', 'http://www.w3.org/1998/Math/MathML')

xml = xmlParser.ElementTree()
rootNode = xml.parse( inputFile )

# do parsing
parseDoc(rootNode, 1)
addTOC(rootNode)

# write output xhtmlfile
outputFile.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
outputFile.write('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1 plus MathML 2.0 plus SVG 1.1//EN"
    "http://www.w3.org/2002/04/xhtml-math-svg/xhtml-math-svg.dtd"[ <!ENTITY % MATHML.prefixed "INCLUDE" > ]>\n''')
outputFile.write(xmlParser.tostring(rootNode, encoding="unicode"))
