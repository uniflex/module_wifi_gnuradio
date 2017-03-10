import os
import sh
import time
import logging
import pyric.utils.channels as channels
import uniflex_module_gnuradio
from uniflex.core import modules

__author__ = "Anatolij Zubow, Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow, gawlowicz}@tkn.tu-berlin.de"


class WiFiGnuRadioModule(uniflex_module_gnuradio.GnuRadioModule):
    """
        WiFi GNURadio connector module.
        IEEE 802.11 WiFi implemented in GnuRadio.
        Implementation is based on https://github.com/bastibl/gr-ieee802-11

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
        1) activate the radio program using activate_radio_program
           (gr_scripts/uniflex_wifi_transceiver.grc)
        2) read/write parameters
    """

    def __init__(self, usrp_addr="addr=192.168.30.2",
                 ctrl_socket_host="localhost",
                 ctrl_socket_port=8080,
                 src_mac="12:34:56:78:90:ab",
                 dst_mac="30:14:4a:e6:46:e4",
                 bss_mac="66:66:66:66:66:66",
                 src_ipv4_address="192.168.123.1",
                 dst_ipv4_address="192.168.123.2",
                 gnu_rp_name="uniflex_wifi_transceiver"):

        super(WiFiGnuRadioModule, self).__init__(usrp_addr, ctrl_socket_host,
                                                 ctrl_socket_port)

        self.log = logging.getLogger('WiFiGnuRadioModule')
        self.uniflex_path = os.environ['UNIFLEX_PATH']
        self.grc_radio_program_name = gnu_rp_name

        self.fid = open(os.path.join(self.uniflex_path, "modules", "wifi_gnuradio", "gr_scripts", gnu_rp_name + ".grc"))
        self.grc_xml = self.fid.read()

        # WiFi Configuration
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.bss_mac = bss_mac
        self.src_ipv4_address = src_ipv4_address
        self.dst_ipv4_address = dst_ipv4_address

        sh_logger = logging.getLogger('sh.command')
        sh_logger.setLevel(logging.CRITICAL)

    @modules.on_start()
    def _activate_rp(self):
        self.log.info('Activate GR80211 radio program')
        self.activate_radio_program(self.grc_radio_program_name, self.grc_xml)

        tapIface = "tap0"
        while True:
            try:
                time.sleep(1)
                sh.ifconfig(tapIface)
                break
            except sh.ErrorReturnCode_1:
                self.log.debug("Waiting for device: {}".format(tapIface))

        self.set_src_mac(self.src_mac)
        self.set_dst_mac(self.dst_mac)
        self.set_bss_mac(self.bss_mac)

        # configure interface
        sh.ifconfig(tapIface, "down")
        sh.ifconfig(tapIface, "hw", "ether", self.src_mac)
        sh.ifconfig(tapIface, "mtu", 440)
        sh.ifconfig(tapIface, self.src_ipv4_address, "netmask", "255.255.255.0", "up")

        # configure routing
        sh.route("del", "-net", "192.168.123.0/24")
        sh.route("add", "-net", "192.168.123.0/24", "mss", "400", "dev", tapIface)

        # configure arp
        sh.arp("-s", self.dst_ipv4_address, self.dst_mac)

    def deactivate_radio_program(self, grc_radio_program_name=None, do_pause=False):
        # override
        super(WiFiGnuRadioModule, self).deactivate_radio_program(self.grc_radio_program_name, False)

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

    def _convert_mac(self, mac):
        return str(list(map(lambda x: hex(int(x, 16)), mac.split(":"))))

    def set_src_mac(self, mac_addr, ifaceName=None):
        self.log.info('Set SRC MAC address to {}'.format(mac_addr))
        mac_addr = self._convert_mac(mac_addr)
        inval = {}
        inval['src_mac'] = mac_addr
        self.set_parameters(inval)

    def get_src_mac(self, ifaceName=None):
        self.log.info('Get SRC MAC address')
        gvals = ['src_mac']
        src_mac = self.get_parameters(gvals)
        return src_mac

    def set_dst_mac(self, mac_addr, ifaceName=None):
        self.log.info('Set DST MAC address to {}'.format(mac_addr))
        mac_addr = self._convert_mac(mac_addr)
        inval = {}
        inval['dst_mac'] = mac_addr
        self.set_parameters(inval)

    def get_dst_mac(self, ifaceName=None):
        self.log.info('Get DST MAC address')
        gvals = ['dst_mac']
        dst_mac = self.get_parameters(gvals)
        return dst_mac

    def set_bss_mac(self, mac_addr, ifaceName=None):
        self.log.info('Set BSS MAC address to {}'.format(mac_addr))
        mac_addr = self._convert_mac(mac_addr)
        inval = {}
        inval['bss_mac'] = mac_addr
        self.set_parameters(inval)

    def get_bss_mac(self, ifaceName=None):
        self.log.info('Get BSS MAC address')
        gvals = ['bss_mac']
        bss_mac = self.get_parameters(gvals)
        return bss_mac
