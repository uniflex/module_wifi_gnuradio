#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import uniflex_module_gnuradio

'''
    Direct module test; without framework.
    Req.:
    - GnuRadio has to be installed: apt-get install gnuradio
    - GR80211 module (https://github.com/bastibl/gr-ieee802-11)
'''
if __name__ == '__main__':

    grm = uniflex_module_gnuradio.GnuRadioModule()

    fid = open(os.path.join(os.path.expanduser("../"), "gr_scripts", "uniflex_wifi_transceiver.grc"))
    grc_xml = fid.read()

    # print(grc_xml)

    grc_radio_program_name = 'gr-ieee802-11'
    inval = {}
    inval['ID'] = 1
    inval['grc_radio_program_code'] = grc_xml

    grm.activate_radio_program(grc_radio_program_name, **inval)

    time.sleep(2)
    if True:

        for ii in range(5):
            res = grm.get_channel(None)
            print(res)
            res = grm.get_bandwidth(None)
            print(res)

    tvals = {}
    tvals['do_pause'] = str(True)
    grm.deactivate_radio_program(grc_radio_program_name, **tvals)
