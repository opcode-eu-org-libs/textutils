About this repository
=====================

This is collection of text proccessing utils, primarily created for my website.

Some of the tools in this repo:

* [diff.py](compare/diff.py) – compare two files by sections (find section from file A in file B and compare it)
* [tex2pdf.sh](convert/tex2pdf.sh) – build LaTeX with lualatex until stop changing toc and references
* [xhtml2pdf.sh](convert/xhtml2pdf.sh) and [toc2pdf.py](convert/toc2pdf.py) – convert XHTML to PDF using wkhtmltopdf
  and create table of content as pdf bookmarks
* [xml2xhtml.py](convert/xml2xhtml.py) – prepare XHTML documents (convert some xml tags,
  convert LaTeX equations to MathML, include and prepare for hightligt source codes files and generate table of contents)
* [add_md5_to_pdf.sh](misc/add_md5_to_pdf.sh) – add overlay md5sum and source filename info to pdf file (for printing)


## License

	Copyright © 2003-2019, Robert Ryszard Paciorek <rrp@opcode.eu.org>
	
	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:
	 
	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.
	 
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.
