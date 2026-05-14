import sys
import importlib
import inspect
from pathlib import Path

# -- Path setup --------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / 'src'))

# Symlink README.md into this directory so index.md can include it.
_readme_link = Path(__file__).parent / 'README.md'
if not _readme_link.exists():
    _readme_link.unlink(missing_ok=True)  # remove stale symlink from prior build
    _readme_link.symlink_to(_PROJECT_ROOT / 'README.md')

# -- Project information -----------------------------------------------------
import deep_dataclasses

project = 'deep_dataclasses'
author = 'Anguelos Nicolaou'
copyright = '2024, Anguelos Nicolaou'
release = deep_dataclasses.__version__
version = '.'.join(release.split('.')[:2])

exclude_patterns = ['_build', 'README.md']

# -- Extensions --------------------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.linkcode',
    'myst_parser',
    'sphinx_copybutton',
]

# -- Napoleon: NumPy docstring style -----------------------------------------
napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# -- Autodoc -----------------------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'

# -- MyST --------------------------------------------------------------------
myst_enable_extensions = ['colon_fence', 'deflist']
myst_heading_anchors = 3
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}

# -- HTML --------------------------------------------------------------------
html_theme = 'furo'
html_title = 'deep_dataclasses'

# -- Copy button -------------------------------------------------------------
copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True
copybutton_exclude = '.linenos'

# -- Linkcode: [source] buttons linking to GitHub ----------------------------
_GITHUB_ROOT = 'https://github.com/anguelos/deep_dataclasses/blob/main'


def linkcode_resolve(domain, info):
    if domain != 'py' or not info.get('module'):
        return None
    try:
        mod = importlib.import_module(info['module'])
        obj = mod
        for part in info['fullname'].split('.'):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        src_file = Path(inspect.getfile(obj))
        lines, start = inspect.getsourcelines(obj)
        end = start + len(lines) - 1
        parts = src_file.parts
        try:
            rel = Path(*parts[parts.index('src'):])
        except ValueError:
            rel = src_file.name
        return f'{_GITHUB_ROOT}/{rel}#L{start}-L{end}'
    except Exception:
        return None


# -- LaTeX / PDF -------------------------------------------------------------
# Shields.io badge URLs contain paths like "tests.yml?label=tests"; Sphinx
# derives a local filename from the URL path, giving LaTeX a .yml file it
# cannot handle.  Restricting recognised graphics extensions to raster/vector
# formats that pdflatex actually supports causes it to silently skip anything
# else (badges, .yml artefacts, etc.) instead of hard-erroring.
latex_elements = {
    'preamble': r'\DeclareGraphicsExtensions{.pdf,.png,.jpg,.jpeg}',
}

# Suppress the matching Sphinx-level warning for remote images that can't be
# fetched or whose format isn't supported by the current builder.
suppress_warnings = ["image.not_readable", "image.not_supported"]
