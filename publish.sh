#!/bin/bash

# Clean previous builds
rm -rf dist/

# Make sure we have the latest Poetry
pip install --upgrade poetry

# Build the package
poetry build

# Check the distribution
poetry check

# Upload to TestPyPI (optional)
# poetry publish --repository testpypi

# Upload to PyPI
# Uncomment the following line when ready to publish to PyPI
# poetry publish 