#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
#

"""OpusLib Package."""

import ctypes  # type: ignore
from ctypes.util import find_library  # type: ignore

__author__ = 'Никита Кузнецов <self@svartalf.info>'
__copyright__ = 'Copyright (c) 2012, SvartalF'
__license__ = 'BSD 3-Clause License'


import os
import sys

lib_location = find_library('opus')

if lib_location is None:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        for name in ['libopus.dylib', 'libopus.0.dylib', 'libopus.so.0']:
            path = os.path.join(sys._MEIPASS, name)
            if os.path.exists(path):
                lib_location = path
                break

if lib_location is None:
    raise Exception('Could not find Opus library. Make sure it is installed.')

libopus = ctypes.CDLL(lib_location)

c_int_pointer = ctypes.POINTER(ctypes.c_int)
c_int16_pointer = ctypes.POINTER(ctypes.c_int16)
c_float_pointer = ctypes.POINTER(ctypes.c_float)
c_ubyte_pointer = ctypes.POINTER(ctypes.c_ubyte)
