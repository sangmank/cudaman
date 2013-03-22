CUDAMAN: CUDA API Reference to Man Pages
========================================

CUDA Toolkit no longer provides official man page, and only provides
reference in PDF files. There are web pages, but it is hard to look
up. 

CUDAMAN makes CUDA API search easier by generating man pages out of
the official CUDA reference web pages and installing them.

To use CUDAMAN, you need to firstly generate the man pages, copy the
man pages to appropriate locations, and register them to `man-db`. You
can do this in one step, by simply running `make; make install`.


Prerequisite
============

- Make
- wget
- python 2.6 or 2.7
- libxml2 module for python
- pandoc

On debian or Ubuntu, you can install these dependencies using:

    apt-get install python-libxml2 pandoc make wget


Generating man pages
====================
Simply type:

    make 

By default, this creates man pages in `./out` directory. You can
change the directory by giving OUT_DIR option:

    make OUT_DIR=../cuda_man


Installing man pages
===================
Simply type:

    make install

By default, this copies man pages into ~/man/man3 directory,
compresses them, and register them to man-db. You can change the
installation path by giving INSTALL_DIR like

    make install INSTALL_DIR=/usr/share/man/man3

If you gave OUT_DIR to `make` in the previous step, you also need to
give the same option here as well.