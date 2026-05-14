SPHINXBUILD = sphinx-build
SOURCEDIR   = ./doc
BUILDDIR    = ./doc/_build

.PHONY: help html clean

help:
	@$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR)

html:
	@$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo "Build finished: $(BUILDDIR)/html/index.html"

clean:
	rm -rf $(BUILDDIR)
