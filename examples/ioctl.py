#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import logging
import ctypes
import struct

from collections import defaultdict
from errno import ENOENT, ENOTTY
from stat import S_IFDIR, S_IFREG
from sys import argv, exit
from time import time
from ioctl_opt import IOWR

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

if not hasattr(__builtins__, 'bytes'):
    bytes = str

class Ioctl(LoggingMixIn, Operations):
    'Example filesystem based on memory.py to demonstrate ioctl().'

    def __init__(self):
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2)

    def create(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                                st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time())

        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        return self.files[path]

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def readdir(self, path, fh):
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']

    def ioctl(self, path, cmd, arg, fh, flags, data):
        M_IOWR = IOWR(ord('M'), 1, ctypes.c_uint32)
        if cmd == M_IOWR:
            inbuf = ctypes.create_string_buffer(4)
            ctypes.memmove(inbuf, data, 4)
            data_in = struct.unpack('<I', inbuf)[0]
            data_out = data_in + 1
            outbuf = struct.pack('<I', data_out)
            ctypes.memmove(data, outbuf, 4)
        else:
            raise FuseOSError(ENOTTY)
        return 0


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(Ioctl(), argv[1], foreground=True)
