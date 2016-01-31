#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import codecs
import os


def main():  # pragma: no cover
    here = os.path.abspath(os.path.dirname(__file__))
    fil = os.path.join(here, '../tests/models.py')
    with codecs.open(fil, encoding='utf-8') as fil:
        scaffold = fil.read()
    print(scaffold)

if __name__ == "__main__":  # pragma: no cover
    main()
