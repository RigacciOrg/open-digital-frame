TARGET = open_digital_frame
PREFIX = $(DESTDIR)/usr/local
BINDIR = $(PREFIX)/bin

BIN_FILES = open-digital-frame photo-reframe
BIN_SCRIPTS = photo-info photo-share screensaver-off screensaver-on

PYTHON_VERSION := $(shell python --version | awk '{print $$2}' | cut -f1,2 -d.)
PYTHON_DIR = $(PREFIX)/lib/python$(PYTHON_VERSION)/dist-packages
PYTHON_MODS = __init__.py odf.py
PY_RES_ADDONS := $(shell cd open_digital_frame/resources/addons; echo *.py)
PY_RES_IMAGES := $(shell cd open_digital_frame/resources/img; echo *.png)

.PHONY: install
install: install-python

.PHONY: install-python
install-python:
	install -m 755 -o root -g root -D -t $(BINDIR) $(addprefix bin/, $(BIN_FILES))
	install -m 644 -o root -g root -D -t $(PYTHON_DIR)/$(TARGET) $(addprefix open_digital_frame/, $(PYTHON_MODS))
	install -m 644 -o root -g root -D -t $(PYTHON_DIR)/$(TARGET)/resources/addons $(addprefix open_digital_frame/resources/addons/, $(PY_RES_ADDONS))
	install -m 644 -o root -g root -D -t $(PYTHON_DIR)/$(TARGET)/resources/img $(addprefix open_digital_frame/resources/img/, $(PY_RES_IMAGES))
	python -m py_compile $(PYTHON_DIR)/$(TARGET)/*.py
	python -m py_compile $(PYTHON_DIR)/$(TARGET)/resources/addons/*.py

.PHONY: install-utils
install-utils:
	install -m 755 -o root -g root -D $(BINDIR) $(addprefix bin/, $(BIN_SCRIPTS))

.PHONY: uninstall
uninstall:
	-rm -f  $(addprefix $(BINDIR)/, $(BIN_FILES))
	-rm -f  $(addprefix $(BINDIR)/, $(BIN_SCRIPTS))
	-rm -rf $(PYTHON_DIR)/$(TARGET)
