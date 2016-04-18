from module_gnuradio import SecureGnuRadioModule
import os
import time
if __name__ == '__main__':

    grm = SecureGnuRadioModule()
    fid = open(os.path.join(os.path.expanduser("."), "testdata", "test_TX.grc"))
    grc_xml = fid.read()
    #print(grc_xml)
    inval = {}
    inval['ID'] = 11
    inval['grc_radio_program_name'] = 'test_TX.grc'
    inval['grc_radio_program_code'] = grc_xml
    #print(inval.get('grc_radio_program_name'))
    #print(inval.get('grc_radio_program_code'))


    grm.set_inactive(**inval)



