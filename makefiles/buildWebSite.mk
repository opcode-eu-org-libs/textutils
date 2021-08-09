# Core makefile for opcode.eu.org repos (require GNU Make)
#  * prepare build and output directories
#  * convert .xml to XHTML files
#  * create PDF files from LaTeX or XHTML files

# Copyright (c) 2019-2020 Robert Ryszard Paciorek <rrp@opcode.eu.org>
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


# file should be included in other Makefiles by
#  include path/to/this.file
#
# parent Makefile must define next variaibles:
#  OUTDIR      := path to output webpage directory
#  TEXBUILDDIR := path to temporary build dir for LaTeX
#  LIBFILESDIR := path to the directory containing $(LIBFILES)
#  SVGICONSDIR := path to the directory containing $(SVGICONS)
#  or
#  SVGICONURL  := base URL to download $(SVGICONS)
#
# all following variables can be override in parent Makefile by:
#  override VARIABLE_NAME := new values

LIBFILES   := base.css menu.css index.css menu.js opcode.svg
SVGICONS   := gitRepo.svg htmlFile.svg pdfFile.svg webSite.svg
IMGSRC     := images-src
EXTRAPDF   := teacher

# add converting scripts from TextUtils to PATH
TEXTUTILS  := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
export PATH := $(TEXTUTILS)/convert:$(PATH)


#
# buils all .xml and .tex files in current dir by default
#

.PHONY: buildAll
buildAll: $(basename $(wildcard *.xml)) $(basename $(wildcard *.tex))

.PHONY: clean
clean:
	rm -fr "$(OUTDIR)" "$(TEXBUILDDIR)"


#
# macros to add dependencies from files in $(IMGSRC)
#

img4xml_from_src = $(patsubst $(IMGSRC)/%,$(OUTDIR)/img/%,$(addsuffix .svg,$(basename $(wildcard $(IMGSRC)/$(1)))))
img4tex_from_src = $(patsubst $(IMGSRC)/%,$(TEXBUILDDIR)/img/%,$(addsuffix .pdf,$(basename $(wildcard $(IMGSRC)/$(1)))))
# usage: $(call img4tex_from_src,GLOB_IN_IMGSRC_DIR)
#
# 1. get list of path to all files in $(IMGSRC) matching to GLOB_IN_IMGSRC_DIR (via wildcard)
# 2. replace filename extension by .pdf (via basename and addsuffix)
# 3. replace $(IMGSRC) by OUTPUT_OR_BUILD_DIR/img (via patsubst)


#
# prepare $(OUTDIR)
#

# generate highlight.css
$(OUTDIR)/lib/highlight.css:
	mkdir -p "$(@D)"
	python3 -c 'from pygments.formatters import HtmlFormatter; print(HtmlFormatter().get_style_defs(".pygments"))' > "$@"

# link or download _external_ svg icons to $(OUTDIR)/lib
$(addprefix $(OUTDIR)/lib/, $(SVGICONS)):
	mkdir -p "$(@D)"
	if [ -e "$(SVGICONSDIR)/$(@F)" ]; then \
		ln -sf "$$(realpath "$(SVGICONSDIR)/$(@F)")" "$@"; \
	else \
		wget -O "$@" "$(SVGICONURL)/$(@F)"; \
	fi

# link „lib” files from $(LIBFILESDIR) to $(OUTDIR)/lib
$(OUTDIR)/lib/%:
	mkdir -p "$(@D)"
	ln -sf "$$(realpath "$(LIBFILESDIR)/$(@F)")" "$@"

# generate .svg from gEDA .sch
$(OUTDIR)/img/%.svg: $(IMGSRC)/%.sch
	mkdir -p "$(@D)"
	cd "$(@D)"; sch2svg "$(PWD)/$<"

# generate .svg from .tex
$(OUTDIR)/img/%.svg: $(IMGSRC)/%.tex | TeXBuildDir
	$(eval FILEPATH := $(patsubst %$(<F),%,$(patsubst $(IMGSRC)/%,%,$(<))))
	mkdir -p "$(TEXBUILDDIR)/$(FILEPATH)"
	mkdir -p "$(@D)"
	cd "$(TEXBUILDDIR)/$(FILEPATH)" && tex2svg.sh "$(PWD)/$<" "-shell-escape" && mv "$(@F)" "$@"

# generate .svg from .gnuplot
$(OUTDIR)/img/%.svg: $(IMGSRC)/%.gnuplot
	mkdir -p "$(@D)"
	cd "$(@D)"; gnuplot -p "$(PWD)/$<"

# prepare $(OUTDIR) and link files from extra-web-files to $(OUTDIR)
.PHONY: OutDir
OutDir: $(addprefix $(OUTDIR)/lib/, highlight.css $(LIBFILES) $(SVGICONS))
	if [ -d extra-web-files ]; then \
		for f in extra-web-files/*; do \
			if [ -e "$$f" ]; then ln -sf "$$(realpath "$$f")" $(OUTDIR); fi; \
		done \
	fi


#
# prepare $(TEXBUILDDIR)
#

# link .tex and .cls „lib” files from $(LIBFILESDIR) to $(TEXBUILDDIR)
$(TEXBUILDDIR)/%.tex $(TEXBUILDDIR)/%.cls:
	mkdir -p $(TEXBUILDDIR)
	ln -sf "$$(realpath "$(LIBFILESDIR)/$(@F)")" "$@"

# generate .pdf from gEDA .sch
$(TEXBUILDDIR)/img/%.pdf: $(IMGSRC)/%.sch
	mkdir -p "$(@D)"
	cd "$(@D)"; sch2pdf "$(PWD)/$<"

# generate .pdf from .svg
$(TEXBUILDDIR)/img/%.pdf: $(IMGSRC)/%.svg
	mkdir -p "$(@D)"
	inkscape $^ --export-pdf=$@

# generate .pdf from .gnuplot
$(TEXBUILDDIR)/img/%.pdf: $(IMGSRC)/%.gnuplot
	mkdir -p "$(@D)"
	cd "$(@D)"; gnuplot -p "$(PWD)/$<"
	inkscape $(basename $@).svg --export-pdf=$@

# prepare $(TEXBUILDDIR) and link files from extra-tex-files to $(TEXBUILDDIR)
.PHONY: TeXBuildDir
TeXBuildDir: $(TEXBUILDDIR)/pdfBooklets.cls $(TEXBUILDDIR)/LaTeX-demos-examples.tex
	mkdir -p $(OUTDIR)
	if [ -d extra-tex-files ]; then \
		for f in extra-tex-files/*; do \
			if [ -e "$$f" ]; then ln -sf "$$(realpath "$$f")" $(TEXBUILDDIR); fi; \
		done \
	fi


#
# create XHTML and PDF files
#

.DELETE_ON_ERROR:

# build XHTML from XML
$(OUTDIR)/%.xhtml: %.xml  $(patsubst %,OutDir,$(FORCE)) | OutDir
	rm -f "$(basename $@).pdf" "$@"
	xml2xhtml.py "$<" "$@"
	chmod 444 "$@"

# build PDF from XHTML
$(OUTDIR)/%.pdf: $(OUTDIR)/%.xhtml $(patsubst %,OutDir,$(FORCE)) | OutDir
	rm -f "$@"
	xhtml2pdf.sh "$<" "$@"
	chmod 444 "$@"

# build PDF from LaTeX
$(OUTDIR)/%.pdf: %.tex $(patsubst %,TeXBuildDir,$(FORCE)) | TeXBuildDir
	rm -f "$@"
	ln -sf "$$(realpath "$(PWD)/$<")" "$(TEXBUILDDIR)/"
	cd "$(TEXBUILDDIR)"; tex2pdf.sh "$<" "-shell-escape"
	mv "$(TEXBUILDDIR)/$(@F)" "$@"

# build alternative versions of PDF from LaTeX
# $(OUTDIR)/%.pdf is required for dependency tracking
$(addprefix $(OUTDIR)/%--, $(addsuffix .pdf, $(EXTRAPDF))): %.tex $(OUTDIR)/%.pdf $(patsubst %,TeXBuildDir,$(FORCE)) | TeXBuildDir
	rm -f "$@"
	ln -sf "$$(realpath "$(PWD)/$<")" "$(TEXBUILDDIR)/"
	$(eval INPUTNAME := $(basename $(@F)))
	INPUTNAME=$(INPUTNAME); ln -sf "$$(realpath "$(LIBFILESDIR)/$${INPUTNAME#*--}-version.tex")" "$(TEXBUILDDIR)/$(INPUTNAME).tex";
	cd "$(TEXBUILDDIR)"; tex2pdf.sh "$(INPUTNAME).tex" "-shell-escape"
	mv "$(TEXBUILDDIR)/$(@F)" "$@"


#
# alias target for creating XHTML and PDF files
#

.SECONDARY:

%.xhtml : $(OUTDIR)/%.xhtml
	@

%.pdf : $(OUTDIR)/%.pdf
	@

% : %.pdf
	@ if [ -f $(OUTDIR)/$@.xhtml ]; then echo "XHTML saved as $(OUTDIR)/$@.xhtml"; fi
	@ if [ -f $(OUTDIR)/$@.pdf   ]; then echo "PDF   saved as $(OUTDIR)/$@.pdf"; fi
