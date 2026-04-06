SPHINXOPTS    ?=
SOURCEDIR     = .
BUILDDIR      = _build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

html:
	sphinx-build -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)

clean:
	rm -rf "$(BUILDDIR)"

.PHONY: help html clean Makefile
