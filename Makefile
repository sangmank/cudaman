SECTION ?= 3
OUT_DIR ?= out
INSTALL_DIR ?= ~/man/man$(SECTION)

SHELL := /bin/bash

TARGETS := cuda-driver-api.done cuda-runtime-api.done cuda-math-api.done

all: $(OUT_DIR) $(TARGETS)

$(OUT_DIR):
	mkdir -p $(OUT_DIR)

%.html:
	wget http://docs.nvidia.com/cuda/$(@:.html=)/index.html -O $@

%.done: %.html
	./cudaman.py -o $(OUT_DIR) -s $(SECTION) $<
	touch $@

install:
	mkdir -p $(INSTALL_DIR)
	cp -f $(OUT_DIR)/*.$(SECTION) $(INSTALL_DIR)/
	cd $(INSTALL_DIR); for man in *.$(SECTION); do gzip -f $${man}; done
	mandb

clean:
	rm $(TARGETS)