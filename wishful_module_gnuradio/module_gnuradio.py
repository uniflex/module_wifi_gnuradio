import os
import time
import logging
import random
import wishful_upis as upis
import wishful_framework as wishful_module
import subprocess
import pprint
import xmlrpc.client
from enum import Enum

from generator.rp_combiner import RadioProgramCombiner

__author__ = "A. Zubow"
__copyright__ = "Copyright (c) 2016, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


""" tracking the state of the radio program """
class RadioProgramState(Enum):
    INACTIVE = 1
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4

"""
    Basic GNURadio connector module.
"""
@wishful_module.build_module
class GnuRadioModule(wishful_module.AgentModule):
    def __init__(self):
        super(GnuRadioModule, self).__init__()

        self.log = logging.getLogger('gnuradio_module.main')

        self.gr_radio_programs = {}
        self.gr_process = None
        self.gr_process_io = None
        self.gr_radio_programs_path = os.path.join(os.path.expanduser("~"), ".wishful", "radio")
        if not os.path.exists(self.gr_radio_programs_path):
            os.makedirs(self.gr_radio_programs_path)
            self.build_radio_program_dict()

        # config values
        self.ctrl_socket_host = "localhost"
        self.ctrl_socket_port = 8080
        self.ctrl_socket = None

        self.gr_state = RadioProgramState.INACTIVE

        self.combiner = None
        self.log.debug('initialized ...')


    @wishful_module.bind_function(upis.radio.add_program)
    def add_program(self, **kwargs):
        """ Serialize radio program to local repository """

        # params
        grc_radio_program_name = kwargs['grc_radio_program_name']  # name of the radio program
        grc_radio_program_code = kwargs['grc_radio_program_code']  # radio program XML flowgraph

        self.log.info("Add radio program %s to local repository" % grc_radio_program_name)

        # serialize radio program XML flowgraph to file
        fid = open(os.path.join(self.gr_radio_programs_path, grc_radio_program_name + '.grc'), 'a')
        fid.write(grc_radio_program_code)
        fid.close()

        # rebuild radio program dictionary
        self.build_radio_program_dict()


    @wishful_module.bind_function(upis.radio.merge_programs)
    def merge_programs(self, **kwargs):
        '''
            Given a set of Gnuradio programs (described as GRC flowgraph) this program combines all
            those radio programs in a single meta radio program which allows very fast switching from
            one protocol to another.
        '''

        # params
        grc_radio_program_names = kwargs['grc_radio_program_names']  # list of radio program names

        self.combiner = RadioProgramCombiner(self.gr_radio_programs_path)

        # make sure all radio programms are already uploaded
        for rp in grc_radio_program_names:
            if rp not in self.gr_radio_programs:
                self.log.warn('Cannot merge missing radio program!!!')
                raise AttributeError("Unknown radio program %s" % rp)
            self.combiner.add_radio_program(rp + '_', rp + '.grc')

        # run generator
        self.combiner.generate()

    @wishful_module.bind_function(upis.radio.switch_program)
    def switch_program(self, target_program_name, **kwargs):
        '''
            Run-time control of meta radio program which allows very fast switching from
            one protocol to another:
            - context switching
        '''

        # open proxy
        proxy = xmlrpc.client.ServerProxy("http://localhost:8080/")

        # load metadata
        proto_usrp_src_dicts = eval(open(os.path.join(self.gr_radio_programs_path, 'meta_rp_proto_dict.txt'), 'r').read())
        usrp_source_fields = eval(open(os.path.join(self.gr_radio_programs_path, 'meta_rp_fields.txt'), 'r').read())

        res = getattr(proxy, "get_session_var")()
        self.log.info('Current proto: %s' % str(res))
        #last_proto = res[0]

        # get IDX of new radio program
        new_proto_idx = self.combiner.get_proto_idx(target_program_name)

        # read variables of new protocol
        init_session_value = []
        init_session_value.append(new_proto_idx)
        for field in usrp_source_fields:
            res = getattr(proxy, "get_%s" % proto_usrp_src_dicts[new_proto_idx][field])()
            init_session_value.append(float(res))

        self.log.info('Switch to protocol %d with cfg %s' % (new_proto_idx, str(init_session_value)))
        getattr(proxy, "set_session_var")(init_session_value)


    @wishful_module.bind_function(upis.radio.remove_program)
    def remove_program(self, **kwargs):
        """ Remove radio program from local repository """

        grc_radio_program_name = kwargs['grc_radio_program_name']  # name of the radio program

        if self.gr_radio_programs is not None and grc_radio_program_name in self.gr_radio_programs:
            os.remove(self.gr_radio_programs[grc_radio_program_name])
            os.rmdir(os.path.join(self.gr_radio_programs_path, grc_radio_program_name))
            os.remove(os.path.join(self.gr_radio_programs_path, grc_radio_program_name + '.grc'))


    @wishful_module.bind_function(upis.radio.set_active)
    def set_active(self, **kwargs):

        # params
        grc_radio_program_name = kwargs['grc_radio_program_name'] # name of the radio program

        if self.gr_state == RadioProgramState.INACTIVE:
            self.log.info("Start new radio program")
            self.ctrl_socket = None

            """Launches Gnuradio in background"""
            if self.gr_radio_programs is None or grc_radio_program_name not in self.gr_radio_programs:
                # serialize radio program to local repository
                self.add_program(kwargs)
            if self.gr_process_io is None:
                self.gr_process_io = {'stdout': open('/tmp/gnuradio.log', 'w+'), 'stderr': open('/tmp/gnuradio-err.log', 'w+')}
            if grc_radio_program_name not in self.gr_radio_programs:
                self.log.error("Available layers: %s" % ", ".join(self.gr_radio_programs.keys()))
                raise AttributeError("Unknown radio program %s" % grc_radio_program_name)
            if self.gr_process is not None:
                # An instance is already running
                self.gr_process.kill()
                self.gr_process = None
            try:
                # start GNURadio process
                self.gr_radio_program_name = grc_radio_program_name
                self.gr_process = subprocess.Popen(["env", "python2", self.gr_radio_programs[grc_radio_program_name]],
                                                   stdout=self.gr_process_io['stdout'], stderr=self.gr_process_io['stderr'])
                self.gr_state = RadioProgramState.RUNNING
            except OSError:
                return False
            return True

        elif self.gr_state == RadioProgramState.PAUSED and self.gr_radio_program_name == grc_radio_program_name:
            # wakeup
            self.log.info('Wakeup radio program')
            self.init_proxy()
            try:
                self.ctrl_socket.start()
                self.gr_state = RadioProgramState.RUNNING
            except xmlrpc.Fault as e:
                self.log.error("ERROR: %s" % e.faultString)
        else:
            self.log.warn('Please deactive old radio program before activating a new one.')


    @wishful_module.bind_function(upis.radio.set_inactive)
    def set_inactive(self, **kwargs):

        pause_rp =  bool(kwargs['do_pause'])

        if self.gr_state == RadioProgramState.RUNNING or self.gr_state == RadioProgramState.PAUSED:

            if pause_rp:
                self.log.info("pausing radio program")

                self.init_proxy()
                self.ctrl_socket.stop()
                self.ctrl_socket.wait()
                self.gr_state = RadioProgramState.PAUSED

            else:
                self.log.info("stopping radio program")

                if self.gr_process is not None and hasattr(self.gr_process, "kill"):
                    self.gr_process.kill()
                if self.gr_process_io is not None and self.gr_process_io is dict:
                    for k in self.gr_process_io.keys():
                        #if self.gr_process_io[k] is file and not self.gr_process_io[k].closed:
                        if not self.gr_process_io[k].closed:
                            self.gr_process_io[k].close()
                            self.gr_process_io[k] = None
                self.gr_state = RadioProgramState.INACTIVE
        else:
            self.log.warn("no running or paused radio program; ignore command")


    @wishful_module.bind_function(upis.radio.set_parameter_lower_layer)
    def gnuradio_set_vars(self, **kwargs):
        if self.gr_state == RadioProgramState.RUNNING or self.gr_state == RadioProgramState.PAUSED:
            self.init_proxy()
            for k, v in kwargs.items():
                try:
                    getattr(self.ctrl_socket, "set_%s" % k)(v)
                except Exception as e:
                    self.log.error("Unknown variable '%s -> %s'" % (k, e))
        else:
            self.log.warn("no running or paused radio program; ignore command")


    @wishful_module.bind_function(upis.radio.get_parameter_lower_layer)
    def gnuradio_get_vars(self, **kwargs):
        if self.gr_state == RadioProgramState.RUNNING or self.gr_state == RadioProgramState.PAUSED:
            rv = {}
            self.init_proxy()
            for k, v in kwargs.items():
                try:
                    res = getattr(self.ctrl_socket, "get_%s" % k)()
                    rv[k] = res
                except Exception as e:
                    self.log.error("Unknown variable '%s -> %s'" % (k, e))
            return rv
        else:
            self.log.warn("no running or paused radio program; ignore command")
            return None


    """ Helper functions """

    def build_radio_program_dict(self):
        """
            Converts the radio program XML flowgraphs into executable python scripts
        """
        self.gr_radio_programs = {}
        grc_files = dict.fromkeys([x.rstrip(".grc") for x in os.listdir(self.gr_radio_programs_path) if x.endswith(".grc")], 0)
        topblocks = dict.fromkeys(
            [x for x in os.listdir(self.gr_radio_programs_path) if os.path.isdir(os.path.join(self.gr_radio_programs_path, x))], 0)
        for x in grc_files.keys():
            grc_files[x] = os.stat(os.path.join(self.gr_radio_programs_path, x + ".grc")).st_mtime
            try:
                os.mkdir(os.path.join(self.gr_radio_programs_path, x))
                topblocks[x] = 0
            except OSError:
                pass
        for x in topblocks.keys():
            topblocks[x] = os.stat(os.path.join(self.gr_radio_programs_path, x, 'top_block.py')).st_mtime if os.path.isfile(
                os.path.join(self.gr_radio_programs_path, x, 'top_block.py')) else 0
        for x in grc_files.keys():
            if grc_files[x] > topblocks[x]:
                outdir = "--directory=%s" % os.path.join(self.gr_radio_programs_path, x)
                input_grc = os.path.join(self.gr_radio_programs_path, x + ".grc")
                try:
                    subprocess.check_call(["grcc", outdir, input_grc])
                except:
                    pass
        for x in topblocks.keys():
            if os.path.isfile(os.path.join(self.gr_radio_programs_path, x, 'top_block.py')):
                self.gr_radio_programs[x] = os.path.join(self.gr_radio_programs_path, x, 'top_block.py')

        self.log.info('gr_radio_programs:\n{}'.format(pprint.pformat(self.gr_radio_programs)))


    def init_proxy(self):
        if self.ctrl_socket == None:
            self.ctrl_socket = xmlrpc.client.ServerProxy("http://%s:%d" % (self.ctrl_socket_host, self.ctrl_socket_port))

"""
    Secure GNURadio connector module which checks whether configuration meets regulation requirements, i.e. used frequency,
    transmit power, ...
"""

class SecureGnuRadioModule(GnuRadioModule):
    def __init__(self):
        super(SecureGnuRadioModule, self).__init__()
        self.log = logging.getLogger('SecureGnuRadioModule')


    @wishful_module.bind_function(upis.radio.set_active)
    def set_active(self, **kwargs):

        """ TODO: do some static checks here """
        if True:
            return super(SecureGnuRadioModule, self).set_active(kwargs)
        else:
            self.log.warn('Not allowed ...')


    @wishful_module.bind_function(upis.radio.set_inactive)
    def set_inactive(self, **kwargs):

        """ TODO: do some static checks here """
        if True:
            return super(SecureGnuRadioModule, self).set_inactive(kwargs)
        else:
            self.log.warn('Not allowed ...')


    @wishful_module.bind_function(upis.radio.set_parameter_lower_layer)
    def gnuradio_set_vars(self, **kwargs):

        """ TODO: do some static checks here """
        if True:
            return super(SecureGnuRadioModule, self).gnuradio_set_vars(kwargs)
        else:
            self.log.warn('Not allowed ...')


    @wishful_module.bind_function(upis.radio.get_parameter_lower_layer)
    def gnuradio_get_vars(self, **kwargs):
        return super(SecureGnuRadioModule, self).gnuradio_get_vars(kwargs)