# Makefile for PySolFC

ifeq ($(OS),Windows_NT)
	path_sep = ;
else
	path_sep = :
endif
export PYTHONPATH := $(PYTHONPATH)$(path_sep)$(CURDIR)

.PHONY: all install dist rpm rules

all:
	@echo "No default target"

install:
	python3 setup.py install

dist: rules
	python3 setup.py sdist

rpm: rules
	python3 setup.py bdist_rpm

rules:
	cd html-src && ./gen-html.py
	cp -r html-src/images html-src/html
	rm -rf data/html
	mv html-src/html data
