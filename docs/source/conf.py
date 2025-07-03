# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'olvy-insight'
copyright = '2025, givemechocopy(jun)'
author = 'givemechocopy(jun)'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

language = 'ko'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))  # 프로젝트 루트 경로

extensions = [
    'sphinx.ext.autodoc',     # docstring 기반 API 문서
    'sphinx.ext.napoleon',    # Google/NumPy 스타일 docstring 해석
    'sphinx.ext.viewcode',    # 소스코드 링크 보기
]
