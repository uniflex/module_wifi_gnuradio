import logging
import random
import time
import queue

import wishful_upis as upis
import wishful_framework as wishful_module
from wishful_framework.classes import exceptions

__author__ = "Felice Di Stolfa"
__copyright__ = "Copyright (c) 2016, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "" #<==== Please update


@wishful_module.build_module
class GnuRadioModule(wishful_module.AgentModule):
    def __init__(self):
        super(GnuRadioModule, self).__init__()
        self.log = logging.getLogger('GnuRadioModule')
        self.channel = 1

    @wishful_module.bind_function(upis.wifi.radio.set_channel)
    def set_channel(self, channel):
        self.log.info("Simple Module sets channel: {} on interface: {}".format(channel, self.interface))
        self.channel = channel
        return ["SET_CHANNEL_OK", channel, 0]


    @wishful_module.bind_function(upis.wifi.radio.get_channel)
    def get_channel(self):
        self.log.debug("Simple Module gets channel of interface: {}".format(self.interface))
        return self.channel