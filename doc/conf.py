# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('../src'))

import sphinx_rtd_theme

# -- Project information -----------------------------------------------------

project = "Ethereum Specification"
copyright = "2021, Ethereum"
author = "Ethereum"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
from ethereum_spec_tools.autoapi_patch import apply_patch
apply_patch()


extensions = [
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "autoapi.extension",
    "undocinclude.extension",
    "picklebuilder.picklebuilder",
    "sphinx_rtd_theme",
    "ethereum_spec_tools.toctree",
]

autoapi_type = "python"
autoapi_dirs = ["../src/ethereum"]
autoapi_template_dir = "_templates/autoapi"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The default language to highlight source code in.
highlight_language = "python3"

# A boolean that decides whether module names are prepended to all object
# names (for object types where a "module" of some kind is defined), e.g.
# for py:function directives.
add_module_names = False

# This value controls how to represent typehints (PEP 484.)
autodoc_typehints = "signature"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

if tags.has("stage0"):
    root_doc = "stage0"
    exclude_patterns.append("index.rst")
    exclude_patterns.append("diffs/**")

    # Avoid generating nodes that'll always differ between hard forks to reduce
    # noise in the diffs.
    autodoc_typehints = "none"
elif tags.has("stage1"):
    root_doc = "index"
    exclude_patterns.append("stage0.rst")

    extensions.append("ethereum_spec_tools.nav")
else:
    raise Exception("Pass either `-t stage0` or `-t stage1` to sphinx-build")


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 3,
    "includehidden": True,
    "titles_only": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_css_files = [
    "css/dropdown.css",
    "css/custom.css",
]

html_js_files = [
    "js/toggle_diffs.js",
]
