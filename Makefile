# Makefile for PySolFC

ifeq ($(OS),Windows_NT)
	path_sep = ;
else
	path_sep = :
endif
export PYTHONPATH := $(PYTHONPATH)$(path_sep)$(CURDIR)

.PHONY: all install dist rpm rules pretest test runtest

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

pretest:
	rm -f tests/individually-importing/*.py tests/unit-generated/*.py # To avoid stray files
	python3 scripts/gen_individual_importing_tests.py

TEST_ENV_PATH = $(CURDIR)$(path_sep)$(CURDIR)/tests/lib
TEST_FILES = tests/style/*.t tests/t/*.py tests/individually-importing/*.py

test runtest: export PERL5LIB := $(PERL5LIB)$(path_sep)$(TEST_ENV_PATH)

test: pretest
	prove $(TEST_FILES)

runtest: pretest
	runprove $(TEST_FILES)
