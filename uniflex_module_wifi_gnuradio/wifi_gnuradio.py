import os
import logging
from enum import Enum
import pyric.utils.channels as channels
import uniflex_module_gnuradio

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


"""
    WiFi GNURadio connector module, i.e. IEEE 802.11 WiFi implemented in GnuRadio. Implementation is
    based on https://github.com/bastibl/gr-ieee802-11

    Supported functionality:
    - all functions from generic GnuRadio module
    - freq
    - samp_rate
    - rx_gain
    - tx_gain
    - encoding *
    - chan_est *
    - lo_offset *
    - * (not yet implemented)

    Howto:
    1) activate the radio program using activate_radio_program(gr_scripts/uniflex_wifi_transceiver.grc)
    2) read/write parameters
"""
class WiFiGnuRadioModule(uniflex_module_gnuradio.GnuRadioModule):
    """
        WiFI GNURadio connector module.
    """
    def __init__(self):
        super(WiFiGnuRadioModule, self).__init__()

        self.log = logging.getLogger('WiFiGnuRadioModule')

    def set_channel(self, channel, ifaceName):
        # convert channel to freq
        freq = channels.ch2rf(channel)

        self.log.info('Setting channel for {}:{} to {}/{}'
                      .format(ifaceName, self.device, channel, freq))

        inval = {}
        inval['freq'] = freq
        # delegate to generic function
        self.set_parameters(inval)


    def get_channel(self, ifaceName):

        self.log.info('Getting channel for {}:{}'
                      .format(ifaceName, self.device))

        gvals = ['freq']
        # delegate to generic function
        freq = self.get_parameters(gvals)

        # convert channel to freq
        ch = channels.rf2ch(int(freq))

        return ch

    def set_tx_power(self, power_dBm, ifaceName):
        # TODO convert power_dBm to tx power of USRP
        power_usrp = power_dBm

        self.log.info('Setting power on iface {}:{} to {}'
                      .format(ifaceName, self.device, str(power_usrp)))

        inval = {}
        inval['tx_gain'] = power_usrp
        # delegate to generic function
        self.set_parameters(inval)

    def get_tx_power(self, ifaceName):

        self.log.debug("getting power of interface: {}".format(ifaceName))

        gvals = ['tx_gain']
        # delegate to generic function
        tx_gain = self.get_parameters(gvals)

        # TODO convert to dBm
        tx_gain_dBm = tx_gain

        return tx_gain_dBm


    def set_bandwidth(self, bw, ifaceName):

        self.log.info('Setting bandwidth on iface {}:{} to {}'
                      .format(ifaceName, self.device, str(bw)))

        inval = {}
        inval['samp_rate'] = bw
        # delegate to generic function
        self.set_parameters(inval)


    def get_bandwidth(self, ifaceName):
        self.log.debug("getting bandwidth of interface: {}".format(ifaceName))

        gvals = ['samp_rate']
        # delegate to generic function
        samp_rate = self.get_parameters(gvals)

        return samp_rate


    def set_rx_gain(self, rx_gain_dBm, ifaceName):
        # TODO convert power_dBm to tx power of USRP
        rx_gain = rx_gain_dBm

        self.log.info('Setting rx gain on iface {}:{} to {}'
                      .format(ifaceName, self.device, str(rx_gain)))

        inval = {}
        inval['rx_gain'] = rx_gain
        # delegate to generic function
        self.set_parameters(inval)


    def get_rx_gain(self, ifaceName):
        self.log.debug("getting rx gain of interface: {}".format(ifaceName))

        gvals = ['rx_gain']
        # delegate to generic function
        rx_gain = self.get_parameters(gvals)

        # TODO convert to dBm
        rx_gain_dBm = rx_gain

        return rx_gain_dBm