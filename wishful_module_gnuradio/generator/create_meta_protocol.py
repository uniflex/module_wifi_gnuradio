#!/usr/bin/env python3

import xml.etree.ElementTree as etree
import string
from ast import literal_eval as make_tuple

'''
    Given a set of Gnuradio programs (described as GRC flowgraph) this program combines all
    those radio programs in a single meta radio program which allows very fast switching from
    one protocol to another.
'''

__author__ = "A. Zubow"
__copyright__ = "Copyright (c) 2016, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"

usrp_source_fields = ['samp_rate', 'center_freq0', 'gain0']

def rename_all_variables(prefix, tree, coord_y_offset):
    root = tree.getroot()

    vars_dict = []
    print('1. step: rename variables ...')

    for block in root.findall('block'):
        block_key = block.find('key')
        #print('block_key: %s' % block_key.text)
        for param in block.findall("param"):
            param_key = param.find("key")
            param_val = param.find("value")
            if param_key.text == 'id':
                old_id = param_val.text
                new_id = prefix + param_val.text
                #print('Replace %s by %s' % (old_id, new_id))
                param_val.text = new_id
                # replace references
                replace_all_references(root, old_id, new_id)
                vars_dict.append(new_id)
            if param_key.text == '_coordinate':
                old_coord = make_tuple(param_val.text)
                yc = old_coord[1] + coord_y_offset
                xc = old_coord[0]
                param_val.text = str((xc, yc))

    return vars_dict

def replace_all_references(root, old_id, new_id):
    # replace all reference in blocks
    for block in root.findall('block'):
        block_key = block.find('key')
        #print('block_key: %s' % block_key.text)
        for param in block.findall("param"):
            param_val = param.find("value")
            param_key = param.find("key")
            if param_key.text != 'id':
                if param_val.text is not None:
                    param_val.text = param_val.text.replace(old_id, new_id)


    # replace all reference in connections
    for conn in root.findall('connection'):
        src_block_id = conn.find("source_block_id")
        if src_block_id.text is not None:
            src_block_id.text = src_block_id.text.replace(old_id, new_id)

        snk_block_id = conn.find("sink_block_id")
        if snk_block_id.text is not None:
            snk_block_id.text = snk_block_id.text.replace(old_id, new_id)

def copy_proto_usrp_src_cfg(root, proto_vars):

    print('2. step: copy old usrp_source config ...')

    usrp_src_dict = {}

    for block in root.findall('block'):
        block_key = block.find('key')

        if block_key.text == 'uhd_usrp_source':
            for param in block.findall("param"):
                param_key = param.find("key")
                param_val = param.find("value")

                if param_key.text in usrp_source_fields:
                    if param_val.text in proto_vars:
                        # it is already a variable; nothing ...
                        # print('usrp_src: %s -> %s' % (param_key.text, param_val.text))
                        usrp_src_dict[param_key.text] = param_val.text

                    else:
                        # we have to create a variable ...
                        print('warning ... not yet implemented')
                        assert False


    return usrp_src_dict

if __name__ == '__main__':
    # global vars

    # open template
    print('0. step: load base config ...')
    base_xfile = '../testdata/gen_stub.grc'
    base_tree = etree.parse(base_xfile)

    new_root = etree.Element("flow_graph")
    common_selector_id = None
    common_blocks_socket_pdu_id = None
    num_protocols = 2

    # copy base blocks to new document
    for base_block in base_tree.getroot().findall('block'):
        new_root.append(base_block)

    # get selector ID
    for base_block in base_tree.getroot().findall('block'):
        block_key = base_block.find('key')

        if block_key.text == 'blks2_selector':
            for param in base_block.findall("param"):
                param_val = param.find("value")
                param_key = param.find("key")
                if param_key.text == 'id':
                    common_selector_id = param_val.text
                # set the number of required output ports
                if param_key.text == 'num_outputs':
                    param_val.text = str(num_protocols)

        if block_key.text == 'blocks_socket_pdu':
            for param in base_block.findall("param"):
                param_val = param.find("value")
                param_key = param.find("key")
                if param_key.text == 'id':
                    common_blocks_socket_pdu_id = param_val.text

    # vars
    old_uhd_usrp_source_id = []
    old_blocks_socket_pdu_id = []
    proto_trees = []
    proto_vars = []
    proto_usrp_src_dicts = []

    for protocol_it in range(num_protocols):

        if protocol_it == 0:
            proto_xfile = '../testdata/t1.grc' #''p1_zwave.grc'
            proto_prefix = 'one_' #''zwaveproto_'
            #proto_xfile = '../testdata/p1_zwave.grc'
            #proto_prefix = 'zwaveproto_'
            coord_y_offset = 250
        elif protocol_it == 1:
            proto_xfile = '../testdata/t2.grc' #''p3_bt4le.grc'
            proto_prefix = 'two_' #''bt4leproto_'
            #proto_xfile = '../testdata/p3_bt4le.grc'
            #proto_prefix = 'bt4leproto_'
            coord_y_offset = 500
        else:
            assert False

        proto_trees.append(etree.parse(proto_xfile))
        proto_vars.append(rename_all_variables(proto_prefix, proto_trees[protocol_it], coord_y_offset))
        proto_usrp_src_dicts.append(copy_proto_usrp_src_cfg(proto_trees[protocol_it].getroot(), proto_vars[protocol_it]))

        print('3. step: copy all blocks/connections from proto to base')

        # do the rewiring: replace old usrp_source by selector
        for proto_block in proto_trees[protocol_it].getroot().findall('block'):
            block_key = proto_block.find('key')

            if block_key.text == 'uhd_usrp_source':
                # skip uhd_usrp_source
                for param in proto_block.findall("param"):
                    param_val = param.find("value")
                    param_key = param.find("key")
                    if param_key.text == 'id':
                        # replace by the new usrp_src
                        old_uhd_usrp_source_id.append(param_val.text)
            elif block_key.text == 'blocks_socket_pdu':
                # skip uhd_usrp_source
                for param in proto_block.findall("param"):
                    param_val = param.find("value")
                    param_key = param.find("key")
                    if param_key.text == 'id':
                        # replace by the new blocks_socket_pdu
                        old_blocks_socket_pdu_id.append(param_val.text)
            else:
                new_root.append(proto_block)

    '''
        Init session variable
    '''
    # get selector ID
    for base_block in new_root.findall('block'):

        init_session_value = '[0'
        for field in usrp_source_fields:
            init_session_value = init_session_value + ',' + proto_usrp_src_dicts[0][field]
        init_session_value = init_session_value + ']'

        block_key = base_block.find('key')

        if block_key.text == 'variable':
            found = False
            for param in base_block.findall("param"):
                param_val = param.find("value")
                param_key = param.find("key")
                if param_key.text == 'id' and param_val.text == 'session_var':
                    found = True

            if found:
                for param in base_block.findall("param"):
                    param_val = param.find("value")
                    param_key = param.find("key")
                    if param_key.text == 'value':
                        param_val.text = init_session_value


    '''
        config connections
    '''
    for base_conn in base_tree.getroot().findall('connection'):
        new_root.append(base_conn)

    for protocol_it in range(num_protocols):

        for proto_conn in proto_trees[protocol_it].getroot().findall('connection'):
            if proto_conn.find('source_block_id').text == old_uhd_usrp_source_id[protocol_it]:
                proto_conn.find('source_block_id').text = common_selector_id
                proto_conn.find('source_key').text = str(protocol_it)

            if proto_conn.find('sink_block_id').text == old_blocks_socket_pdu_id[protocol_it]:
                proto_conn.find('sink_block_id').text = common_blocks_socket_pdu_id
                #proto_conn.find('source_key').text = str(protocol_it)

            new_root.append(proto_conn)


    print('4.step: serialize combined grc file')
    new_tree = etree.ElementTree(new_root)
    new_tree.write('../testdata/all.grc')

    fout = open('../testdata/proto_usrp_src_dicts.txt', 'a')
    fout.write(str(proto_usrp_src_dicts))

    fout = open('../testdata/usrp_source_fields.txt', 'a')
    fout.write(str(usrp_source_fields))