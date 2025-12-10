"""
Setup script for llm-patch package.

This file is provided for backward compatibility.
The package is primarily configured via pyproject.toml.
"""

from setuptools import setup

# Read the contents of README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    long_description=long_description,
    long_description_content_type="text/markdown",
)
