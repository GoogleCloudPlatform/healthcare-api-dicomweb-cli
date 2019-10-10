# -*- coding: utf-8 -*-
"""Wrapper for command line calls of dcmweb
"""
import sys
import fire
from . import dcmweb


def host_wrapper(host, m):  # pylint: disable=invalid-name; disabled because m is also configuration for Fire library and it have to be one letter
    """host - url for dicomWeb
    m - whether to perform batch operations in parallel
    or sequentially, default is in parallel"""
    return dcmweb.Dcmweb(host, m, dcmweb.GoogleAuthenticator())


def main():
    """Main fuction to call dcmweb"""
    if len(sys.argv) > 1 and sys.argv[1] == '-m':
        sys.argv.insert(2, "1")
    else:
        sys.argv.insert(1, "-m")
        sys.argv.insert(2, "0")
    fire.Fire(host_wrapper)
