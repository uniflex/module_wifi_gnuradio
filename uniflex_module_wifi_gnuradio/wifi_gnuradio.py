import os
import pprint
import logging
import subprocess
from enum import Enum
from numpy import arange
import xmlrpc.client

from uniflex.core import modules
import uniflex_module_gnuradio

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


"""
    WiFi GNURadio connector module, i.e. IEEE 802.11 WiFi implemented in GnuRadio.

    Supported functionality:
    - all functions from generic GnuRadio module
    - other: tbd.
"""
class WiFiGnuRadioModule(uniflex_module_gnuradio.GnuRadioModule):
    """
        WiFI GNURadio connector module.
    """
    def __init__(self):
        super(WiFiGnuRadioModule, self).__init__()

        self.log = logging.getLogger('WiFiGnuRadioModule')


    def set_channel(self, channel, ifaceName):
        self.log.info('Setting channel for {}:{} to {}'
                      .format(ifaceName, self.device, channel))

        inval = {}
        inval['freq'] = 5200

        self.set_parameters(inval)
