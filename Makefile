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

BINDIR=/usr/local/bin

help:
	@ echo "USAGE: sudo make installTools"
	@ echo "   or:      make installTools BINDIR=~/mybin"
	@ echo "USAGE: sudo make installDependencies"
	@ echo ""
	@ echo "Install dir for:"
	@ echo " - executables: BINDIR=$(BINDIR)"
	@ echo "You can change them via make variables, as BINDIR above."
	@ echo ""
	@ echo "installDependencies target is dedicated for:"
	@ echo "  Debian 9 (Stretch) and Debian 10 (Buster)"

installTools:
	install -Dt $(BINDIR) convert/*
	install -Dt $(BINDIR) misc/*
	install -Dt $(BINDIR) compare/*


CONVERT_DEP_PKGS=python3-pygments python3  wkhtmltopdf pdftk poppler-utils  texlive-latex-base texlive-luatex texlive-latex-recommended
CONVERT_PIP_PKGS=latex2mathml
MISC_DEP_PKGS=poppler-utils ghostscript pdftk
COMPARE_DEP_PKGS=inotify-tools
installDependencies:
	apt install  $(CONVERT_DEP_PKGS) $(MISC_DEP_PKGS) $(COMPARE_DEP_PKGS) python3-pip
	pip3 install $(CONVERT_PIP_PKGS)
	
	@vers=`dpkg -l poppler-utils | cut -c5- | awk '$$1 == "poppler-utils" {print $$2}'`; \
	 dpkg --compare-versions $$vers ge 0.49 && dpkg --compare-versions $$vers lt 0.74 && \
	 echo "WARNING: bug in pdftohtml (poppler-utils $$vers) broke TOC generation for PDFs" && \
	 echo "         see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=926056" && \
	 echo "         use poppler-utils <= 0.48 or >= 0.74"
