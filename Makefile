.PHONY: clean-pyc clean-build docs requirements

all: help

help:
	@echo "django-editregions version 0.1.0"
	@echo
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "requirements - collect all subrequirements files"
	@echo "test - run tests quickly with the current Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "test-project - launch the test project"
	@echo "check - basic sanity checking of the package"
	@echo "docs - build the sphinx documentation into HTML and JSON"
	@echo "release - package a release"

release: clean requirements
	wget http://b.repl.ca/v1/version-0.1.0-lightgrey.png --output-document=docs/version.png
	python setup.py sdist bdist_wheel
	bumpversion --patch
	twine upload dist/*

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '*~' -exec rm -f {} \;

test: requirements
	python -B -tt -W once setup.py test --failfast

test-all: requirements
	tox

test-project:
	pip install -r test_project/requirements.txt
	python test_project/run.py

requirements:
	rm -f 'requirements.all.txt'
	touch 'requirements.all.txt'
	find . -type f -name requirements.txt ! -path "./.tox/*" ! -path "./test_project/*" -exec cat {} \; | sort -f -d | uniq -u >> requirements.all.txt

check:
	rm -f LONGDESC.html
	python setup.py --long-description | rst2html.py > LONGDESC.html
	@echo
	@echo "Long description written to LONGDESC.html"

docs:
	cd docs && sphinx-build -b html -d _build/doctrees . _build/html
	cd docs && sphinx-build -b json -d _build/doctrees . _build/json
	@echo
	@echo "Sphinx docs generated into HTML and JSON in the _build directory"

