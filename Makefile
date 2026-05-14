SPHINXBUILD  = sphinx-build
SOURCEDIR    = doc
BUILDDIR     = /tmp/deep_dataclasses_doc
SRCDIR       = src
TESTDIR      = test
RUFF_CACHE   = /tmp/ruff_cache_deep_dataclasses
COVDATA      = /tmp/deep_dataclasses_coverage
COVHTML      = /tmp/deep_dataclasses_coverage/html
DISTDIR      = /tmp/deep_dataclasses_dist

.PHONY: test lint autolint doc clean pypi help

help:
	@echo "test     – run all tests with coverage report"
	@echo "lint     – report lint issues (no changes)"
	@echo "autolint – apply auto-fixes (ruff format + ruff --fix)"
	@echo "doc      – build HTML and PDF documentation"
	@echo "clean    – remove all generated temporary directories"
	@echo "pypi     – build and upload to PyPI (bumps version in __init__.py first)"

# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------
clean:
	@for d in $(COVDATA) $(BUILDDIR) $(RUFF_CACHE) $(DISTDIR) dist/; do \
	    [ -e "$$d" ] && chmod -R u+w "$$d" && rm -rf "$$d" && echo "Removed $$d" || true; \
	done

# ---------------------------------------------------------------------------
# pypi  (build + upload)
# ---------------------------------------------------------------------------
pypi: test doc
	@VERSION=$$(python3 -c "import deep_dataclasses; print(deep_dataclasses.__version__)"); \
	 echo "All checks passed. Building version $$VERSION"; \
	 read -p "Press Enter to continue or Ctrl-C to abort..."
	rm -rf $(DISTDIR) && mkdir -p $(DISTDIR)
	python3 -m build --outdir $(DISTDIR)
	twine check $(DISTDIR)/*
	twine upload $(DISTDIR)/*

# ---------------------------------------------------------------------------
# test
# ---------------------------------------------------------------------------
test:
	@mkdir -p $(COVDATA) $(COVHTML)
	COVERAGE_FILE=$(COVDATA)/.coverage \
	python3 -m pytest $(TESTDIR) \
	    --tb=short \
	    --cov=deep_dataclasses \
	    --cov-report=term-missing \
	    --cov-report=html:$(COVHTML)
	@echo ""
	@echo "Coverage HTML: $(COVHTML)/index.html"

# ---------------------------------------------------------------------------
# lint  (read-only: counts issues, no changes)
# ---------------------------------------------------------------------------
lint:
	@echo "=== ruff format (format check) ==="
	@ruff format --check --diff $(SRCDIR) $(TESTDIR) 2>&1 || true
	@echo ""
	@echo "=== ruff check (style / errors) ==="
	@ruff check --cache-dir $(RUFF_CACHE) $(SRCDIR) $(TESTDIR) 2>&1 || true
	@echo ""
	@NFMT=$$(ruff format --check $(SRCDIR) $(TESTDIR) 2>&1 | grep -c "would reformat" || true); \
	 NCHECK=$$(ruff check --cache-dir $(RUFF_CACHE) --output-format concise $(SRCDIR) $(TESTDIR) 2>/dev/null | grep -c "\.py:" || true); \
	 echo "Summary: $$NFMT file(s) need reformatting, $$NCHECK ruff issue(s)"

# ---------------------------------------------------------------------------
# autolint  (applies fixes)
# ---------------------------------------------------------------------------
autolint:
	@echo "=== ruff format ==="
	ruff format $(SRCDIR) $(TESTDIR)
	@echo ""
	@echo "=== ruff check (auto-fix) ==="
	ruff check --cache-dir $(RUFF_CACHE) --fix $(SRCDIR) $(TESTDIR) || true

# ---------------------------------------------------------------------------
# doc  (HTML + PDF via LaTeX)
# ---------------------------------------------------------------------------
doc:
	@echo "=== HTML ==="
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo "HTML: $(BUILDDIR)/html/index.html"
	@echo ""
	@echo "=== PDF (LaTeX) ==="
	$(SPHINXBUILD) -b latex $(SOURCEDIR) $(BUILDDIR)/latex
	-$(MAKE) -C $(BUILDDIR)/latex all-pdf LATEXMKOPTS="-silent" 2>&1 | tail -5
	@PDF=$$(ls $(BUILDDIR)/latex/*.pdf 2>/dev/null | head -1); \
	 if [ -n "$$PDF" ]; then echo "PDF: $$PDF"; else echo "PDF build failed — see $(BUILDDIR)/latex/ for details"; fi
