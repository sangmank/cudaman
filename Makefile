#!/usr/bin/make -f

SECTION ?= 3
OUT_DIR ?= out
INSTALL_DIR ?= ~/man/man$(SECTION)

SHELL := /bin/bash

TARGETS := cuda-driver-api cuda-runtime-api cuda-math-api

OBJS := $(addprefix $(OUT_DIR)/, $(addsuffix .done, $(TARGETS)))

all: $(OUT_DIR) $(OBJS)

$(OUT_DIR):
	mkdir -p $(OUT_DIR)

%.html:
	wget http://docs.nvidia.com/cuda/$(patsubst $(OUT_DIR)/%.html,%, $@)/index.html -O $@

%.done: %.html
	./cudaman.py -o $(OUT_DIR) -s $(SECTION) $<
	touch $@

install:
	mkdir -p $(INSTALL_DIR)
	cp -f $(OUT_DIR)/*.$(SECTION) $(INSTALL_DIR)/
	cd $(INSTALL_DIR); for man in *.$(SECTION); do gzip -f $${man}; done
	mandb

clean:
	rm -f $(OBJS)