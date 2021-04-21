from settings import *
import json
import requests
import pprint
from pvp import pvp
from rosstalk import rosstalk
import logging

logging.basicConfig(level=log_level)


class cue_coder():
    # feed me input strictly from pco app_cues note section, otherwise i might break things!
    # I'll spit out another dictionary with human-readable cue statements.
    def cue_verbose_decoder(*self, cuedict):
        cues_verbose_list = []
        if not cuedict == None:
            for cue in cuedict:
                if cuedict[cue]['device'] in ('CG3', 'CG4'):
                    cue_verbose = f"{cuedict[cue]['device']}:   Cue {cuedict[cue]['cue_name']}"
                    cues_verbose_list.append(cue_verbose)
                if cuedict[cue]['device'] == 'Pause':
                    cue_verbose = f"{cuedict[cue]['device']}:   {cuedict[cue]['time']} seconds."
                    cues_verbose_list.append(cue_verbose)
                if cuedict[cue]['device'] == 'Reminder':
                    cue_verbose = f"{cuedict[cue]['device']}:   " \
                                  f"[{cuedict[cue]['reminder']}]: after {cuedict[cue]['minutes']} minutes," \
                                  f"{cuedict[cue]['seconds']} seconds."
                    cues_verbose_list.append(cue_verbose)
                if cuedict[cue]['device'] == 'Rosstalk':
                    if cuedict[cue]['type'] == 'CC':
                        cue_verbose = f"{cuedict[cue]['device']}:" \
                                      f"   {cuedict[cue]['type']}:{cuedict[cue]['bank']}:{cuedict[cue]['CC']}"
                        cues_verbose_list.append(cue_verbose)
                    if cuedict[cue]['type'] == 'KEYCUT':
                        cue_verbose = f"{cuedict[cue]['device']}:   KeyAuto:" \
                                      f" {cuedict[cue]['bus']}: Key {cuedict[cue]['key']}"
                        cues_verbose_list.append(cue_verbose)
                    if cuedict[cue]['type'] == 'KEYAUTO':
                        cue_verbose = f"{cuedict[cue]['device']}:   KeyAuto:" \
                                      f" {cuedict[cue]['bus']}: Key {cuedict[cue]['key']}"
                        cues_verbose_list.append(cue_verbose)

            return cues_verbose_list

    # feed me data only from the pco 'app cues' section, with data created only from the above function.
    # I'll cue all cues in the dict you give me
    def cue_decoder(*self, cuedict):
        for iteration, cue in enumerate(cuedict):
            # iteration needs to be a string, for use in dict keys... it's dumb
            iteration = str(iteration+1)
            if cuedict[iteration]['device'] in ('CG3', 'CG4'):
                if cuedict[iteration]['device'] == 'CG3':
                    ip = cg3_ip
                    port = cg3_port
                if cuedict[iteration]['device'] == 'CG4':
                    ip = cg4_ip
                    port = cg4_port
                logging.debug(f"Cueing pvp clip. device = {cuedict[iteration]['device']},"
                              f"{cuedict[iteration]['cue_name']}")
                pvp.cue_clip(ip=ip, port=port,
                             playlist=cuedict[iteration]['playlist_index'], clip_number=cuedict[iteration]['cue_index'])
            if cuedict[iteration]['device'] == 'Rosstalk':
                ip = rosstalk_ip
                port = rosstalk_port
                if cuedict[iteration]['type'] == 'CC':
                    command = f"CC {cuedict[iteration]['bank']}:{cuedict[iteration]['CC']}"
                    logging.debug(f"Cueing rosstalk command {command}")
                    rosstalk(rosstalk_ip = ip, rosstalk_port = port, command=command)
            else:
                pass


