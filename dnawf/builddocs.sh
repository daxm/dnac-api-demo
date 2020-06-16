#!/bin/bash
pydoc-markdown docs/pydoc-markdown.yml
cp -r docs/media build/docs/docs/
cp docs/extra.css build/docs/docs/
mkdocs gh-deploy -f build/docs/mkdocs.yml
