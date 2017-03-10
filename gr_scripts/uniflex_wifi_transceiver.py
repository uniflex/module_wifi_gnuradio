#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Uniflex Wifi Transceiver
# Generated: Fri Mar 10 14:35:04 2017
##################################################

import os
import sys
sys.path.append(os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
from wifi_phy_hier import wifi_phy_hier  # grc-generated hier_block
import SimpleXMLRPCServer
import foo
import ieee802_11
import threading
import time


class uniflex_wifi_transceiver(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Uniflex Wifi Transceiver")

        ##################################################
        # Variables
        ##################################################
        self.usrp_addr = usrp_addr = "addr=192.168.10.2"
        self.tx_gain = tx_gain = 0.75
        self.src_mac = src_mac = [0x30, 0x14, 0x4a, 0xe6, 0x46, 0xe4]
        self.samp_rate = samp_rate = 5e6
        self.rx_gain = rx_gain = 0.75
        self.lo_offset = lo_offset = 0
        self.freq = freq = 5890000000
        self.encoding = encoding = 0
        self.dst_mac = dst_mac = [0x12, 0x34, 0x56, 0x78, 0x90, 0xab]
        self.chan_est = chan_est = 0
        self.bss_mac = bss_mac = [0x42, 0x42, 0x42, 0x42, 0x42, 0x42]

        ##################################################
        # Blocks
        ##################################################
        self.xmlrpc_server_0 = SimpleXMLRPCServer.SimpleXMLRPCServer(('localhost', 8080), allow_none=True)
        self.xmlrpc_server_0.register_instance(self)
        self.xmlrpc_server_0_thread = threading.Thread(target=self.xmlrpc_server_0.serve_forever)
        self.xmlrpc_server_0_thread.daemon = True
        self.xmlrpc_server_0_thread.start()
        self.wifi_phy_hier_0 = wifi_phy_hier(
            bandwidth=samp_rate,
            chan_est=chan_est,
            encoding=encoding,
            frequency=freq,
            sensitivity=0.56,
        )
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join((usrp_addr, "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(freq, rf_freq = freq - lo_offset, rf_freq_policy=uhd.tune_request.POLICY_MANUAL), 0)
        self.uhd_usrp_source_0.set_normalized_gain(rx_gain, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	",".join((usrp_addr, "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        	'packet_len',
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)
        self.uhd_usrp_sink_0.set_center_freq(uhd.tune_request(freq, rf_freq = freq - lo_offset, rf_freq_policy=uhd.tune_request.POLICY_MANUAL), 0)
        self.uhd_usrp_sink_0.set_normalized_gain(tx_gain, 0)
        self.ieee802_11_parse_mac_0 = ieee802_11.parse_mac(False, True)
        self.ieee802_11_mac_0 = ieee802_11.mac((src_mac), (dst_mac), (bss_mac))
        self.ieee802_11_ether_encap_0 = ieee802_11.ether_encap(False)
        self.foo_wireshark_connector_0 = foo.wireshark_connector(127, False)
        self.foo_packet_pad2_0 = foo.packet_pad2(False, False, 0.001, 10000, 10000)
        (self.foo_packet_pad2_0).set_min_output_buffer(100000)
        self.blocks_tuntap_pdu_0 = blocks.tuntap_pdu('tap0', 440, False)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0.6, ))
        (self.blocks_multiply_const_vxx_0).set_min_output_buffer(100000)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, '/tmp/wifi.pcap', True)
        self.blocks_file_sink_0.set_unbuffered(True)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tuntap_pdu_0, 'pdus'), (self.ieee802_11_ether_encap_0, 'from tap'))
        self.msg_connect((self.ieee802_11_ether_encap_0, 'to tap'), (self.blocks_tuntap_pdu_0, 'pdus'))
        self.msg_connect((self.ieee802_11_ether_encap_0, 'to wifi'), (self.ieee802_11_mac_0, 'app in'))
        self.msg_connect((self.ieee802_11_mac_0, 'phy out'), (self.wifi_phy_hier_0, 'mac_in'))
        self.msg_connect((self.wifi_phy_hier_0, 'mac_out'), (self.foo_wireshark_connector_0, 'in'))
        self.msg_connect((self.wifi_phy_hier_0, 'mac_out'), (self.ieee802_11_ether_encap_0, 'from wifi'))
        self.msg_connect((self.wifi_phy_hier_0, 'mac_out'), (self.ieee802_11_mac_0, 'phy in'))
        self.msg_connect((self.wifi_phy_hier_0, 'mac_out'), (self.ieee802_11_parse_mac_0, 'in'))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.foo_packet_pad2_0, 0))
        self.connect((self.foo_packet_pad2_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.foo_wireshark_connector_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.wifi_phy_hier_0, 0))
        self.connect((self.wifi_phy_hier_0, 0), (self.blocks_multiply_const_vxx_0, 0))

    def get_usrp_addr(self):
        return self.usrp_addr

    def set_usrp_addr(self, usrp_addr):
        self.usrp_addr = usrp_addr

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.uhd_usrp_sink_0.set_normalized_gain(self.tx_gain, 0)


    def get_src_mac(self):
        return self.src_mac

    def set_src_mac(self, src_mac):
        self.src_mac = src_mac

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.wifi_phy_hier_0.set_bandwidth(self.samp_rate)
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        self.uhd_usrp_source_0.set_normalized_gain(self.rx_gain, 0)


    def get_lo_offset(self):
        return self.lo_offset

    def set_lo_offset(self, lo_offset):
        self.lo_offset = lo_offset
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(self.freq, rf_freq = self.freq - self.lo_offset, rf_freq_policy=uhd.tune_request.POLICY_MANUAL), 0)
        self.uhd_usrp_sink_0.set_center_freq(uhd.tune_request(self.freq, rf_freq = self.freq - self.lo_offset, rf_freq_policy=uhd.tune_request.POLICY_MANUAL), 0)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.wifi_phy_hier_0.set_frequency(self.freq)
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(self.freq, rf_freq = self.freq - self.lo_offset, rf_freq_policy=uhd.tune_request.POLICY_MANUAL), 0)
        self.uhd_usrp_sink_0.set_center_freq(uhd.tune_request(self.freq, rf_freq = self.freq - self.lo_offset, rf_freq_policy=uhd.tune_request.POLICY_MANUAL), 0)

    def get_encoding(self):
        return self.encoding

    def set_encoding(self, encoding):
        self.encoding = encoding
        self.wifi_phy_hier_0.set_encoding(self.encoding)

    def get_dst_mac(self):
        return self.dst_mac

    def set_dst_mac(self, dst_mac):
        self.dst_mac = dst_mac

    def get_chan_est(self):
        return self.chan_est

    def set_chan_est(self, chan_est):
        self.chan_est = chan_est
        self.wifi_phy_hier_0.set_chan_est(self.chan_est)

    def get_bss_mac(self):
        return self.bss_mac

    def set_bss_mac(self, bss_mac):
        self.bss_mac = bss_mac


def main(top_block_cls=uniflex_wifi_transceiver, options=None):

    tb = top_block_cls()
    tb.start()
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
