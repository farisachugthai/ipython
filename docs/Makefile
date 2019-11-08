# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
SRCDIR        = source
BUILDDIR      = build
PYTHON        = python3

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) $(SRCDIR)

# Put it first so that "make" without argument is like "make help".

.PHONY: help clean html htmlhelp changes linkcheck api

default: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html        standalone HTML files"
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

html: api  automagic autogen_shortcuts
html_noapi: clean_api autoconfig automagic autogen_shortcuts

html html_noapi:
	mkdir -p build/html build/doctrees
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) build/html
	@echo
	@echo "Build finished. The HTML pages are in build/html."

automagic: source/interactive/magics-generated.txt

source/interactive/magics-generated.txt: autogen_magics.py
	$(PYTHON) autogen_magics.py
	@echo "Created docs for line & cell magics"

api: source/api/generated/gen.txt

source/api/generated/gen.txt:
	$(PYTHON) autogen_api.py
	# TODO:
	# $(PYTHON) autogen_api_numpy.py
	@echo "Build API docs finished."

autogen_shortcuts: autogen_shortcuts.py ../IPython/terminal/interactiveshell.py source/api/shortcuts.rst
	$(PYTHON) autogen_shortcuts.py
	@echo "Created docs for shortcuts"


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
