# -*- coding: utf-8 -*-
"""
This simple interface calculates md5/sha1 hashes for multiple files in a chosen directory and send them with a
specified reputation via WEB API to the EPO server
"""
__author__ = "Peter Gastinger"
__copyright__ = "Copyright 2016, Raiffeisen Informatik GmbH"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Peter Gastinger"
__email__ = "peter.gastinger@r-it.at"
__status__ = "Development"

# This file needs Python 3.5

# generate .exe with pyinstaller:
cd McAfeeEPO
pyinstaller eporeputations.spec
