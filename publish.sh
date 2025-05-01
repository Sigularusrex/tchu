#!/bin/bash

# Clean previous builds
rm -rf dist/

# Make sure we have the latest Poetry
pip install --upgrade poetry

# Build the package
poetry build

# Check the distribution
poetry check

# If a token is provided via environment variable, configure it
if [ ! -z "$PYPI_TOKEN" ]; then
  echo "Configuring PyPI token from environment variable"
  poetry config pypi-token.pypi "$PYPI_TOKEN"
fi

# Upload to TestPyPI (optional)
# poetry publish --repository testpypi

# Publish to PyPI
# Uncomment the following line when ready to publish to PyPI
# poetry publish

