# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
ALLSPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXAPIDOC   ?= sphinx-apidoc
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
.PHONY: help clean html html_noapi htmlhelp changes linkcheck api

default: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html        standalone HTML files"
	@echo "  html_noapi  HTML files with no API"
	@echo "  htmlhelp    HTML files and a HTML help project"
	@echo "  changes     an overview over all changed/added/deprecated items"
	@echo "  linkcheck   check all external links for integrity (takes a long time)"
	@echo
	@echo "Compound utility targets:"
	@echo "pdf          latex and then runs the PDF generation"
	@echo "all          html and pdf"
	@echo "dist         all, and then puts the results in dist/"

clean_api:
	-rm -rf $(SRCDIR)/api/generated

clean: clean_api
	-rm -rf build/* dist/*
	-rm -f $(SRCDIR)/config/options/config-generated.txt
	-rm -f $(SRCDIR)/config/shortcuts/*.csv
	-rm -f $(SRCDIR)/interactive/magics-generated.txt

pdf: latex
	cd build/latex && make all-pdf

all: html pdf

# For final distribution, only build HTML (our pdf is now so large as to be
# unusable, takes forever to build and just bloats the downloads).  We leave
# them hardlinked at the top-level so users find them easily, though the
# original build/html dir is left in-place (useful to reload builds while
# testing).
dist: html
	rm -rf html
	cp -al build/html .
	@echo "Build finished.  Final docs are in html/"

api:
	$(SPHINXAPIDOC) -e -o source/api/generated ../IPython --tocfile index
	mkdir -p build/html build/doctrees


# In case you couldn't remember, `:r!pydoc sphinx.cmd.build` can be useful here
html:
	$(SPHINXAPIDOC) -b html -c source -e --tocfile index -P -w sphinx.log source build/html
	$(SPHINXBUILD) -b html -c source -P -w sphinx.log $(ALLSPHINXOPTS) source build/html
	@echo
	@echo "Build finished. The HTML pages are in build/html."


html_noapi:
	-rm -rf source/api/generated
	$(SPHINXBUILD) -b html -c source -P -w sphinx.log $(ALLSPHINXOPTS) source build/html
	@echo
	@echo "Build finished. The HTML pages are in build/html."

htmlhelp:
	mkdir -p build/htmlhelp build/doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) build/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in build/htmlhelp."

changes:
	mkdir -p build/changes build/doctrees
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) build/changes
	@echo
	@echo "The overview file is in build/changes."

linkcheck:
	mkdir -p build/linkcheck build/doctrees
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in build/linkcheck/output.rst."
