PROJECT_HOME :=  $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME :=	$(notdir $(patsubst %/, %, $(PROJECT_HOME)))

BUILD_DIR := build
DIST_DIR := dist
TEST_DIR := tests
TEST_FILES := $(wildcard $(TEST_DIR)/*.py)
TEST_TARGETS := $(TEST_FILES:$(TEST_DIR)/%.py=%)
BASIC_CHECKS := pep8 pyflakes
ALL_CHECKS := $(BASIC_CHECKS) pylint
INSTALLED := $(BUILD_DIR)/installed_files.txt
SCRIPT := $(BUILD_DIR)/congist.sh
PYTHON := python3
PIP := pip3

all: check test

$(ALL_CHECKS):
	@if command -v $@ &> /dev/null; \
	 then \
	 	echo checking by $@...; \
    	find $(PROJECT_NAME) -name \*.py | xargs $@; \
	 else \
    	echo $@ is not installed, please run \"$(PIP) install $@\" first; \
    	exit 1; \
     fi;


check: $(BASIC_CHECKS)

check-all: $(ALL_CHECKS)

$(TEST_TARGETS): % : $(TEST_DIR)/%.py
	@py.test -svv $<

test: $(TEST_TARGETS)

test-term:
	@$(PYTHON) setup.py test -v -r term

test-xml:
	@mkdir -p $(BUILD_DIR)
	@$(PYTHON) setup.py test -v -r xml

sonar: test-xml
	@sonar-runner

build:
	@$(PYTHON) setup.py build

install-dev:
	@$(PYTHON) setup.py develop

install:
	@$(PYTHON) setup.py install --record $(INSTALLED)

	@$(eval PY=$(shell cd && $(PIP) show congist | grep -i Location | awk '{print $$2}')/congist/congist_cli.py)
	@echo '$(PYTHON) $(PY) "$$@"' > $(SCRIPT)
	@chmod +x $(SCRIPT)
	@echo generated the ready-to-use script: $(SCRIPT)

uninstall:
	@cat $(INSTALLED) | xargs sudo rm -rf

clean:
	@rm -rf *.egg *.egg-info $(BUILD_DIR)

distclean: clean
	@rm -rf $(DIST_DIR)

realclean: distclean
	@find . -name __pycache__ | xargs rm -rf
	@find . -name \*.pyc | xargs rm -f

.PHONY: all $(TEST_TARGETS) $(ALL_CHECKS) check check-all test test-term \
	test-xml sonar build install-dev install clean distclean realclean
