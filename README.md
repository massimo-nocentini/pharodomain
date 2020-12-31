# pharodomain
A Sphinx domain for Pharo Smalltalk.

According to https://packaging.python.org/tutorials/packaging-projects/, to package me do the following steps:
- create a virtual env and activate it
- run `pip install --upgrade setuptools wheel`
- run `python setup.py sdist bdist_wheel`

For now we don't wont to publish it on the global PIP, therefore to install it locally run `pip install .`.
