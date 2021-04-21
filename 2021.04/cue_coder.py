from settings import *
import json
import requests
import pprint
from pvp import pvp
from rosstalk import rosstalk
import logging
from kipro import kipro

logging.basicConfig(level=log_level)


class cue_coder():
    # feed me input strictly from root pco app_cues note section, otherwise i might break things!
    # I'll spit out another dictionary with human-readable cue statements.
    def cue_verbose_decoder(*self, cuedict):
        cues_verbose_list = []
        if not cuedict == None:
            for cue in cuedict:
                logging.debug('creating verbose output from %s', cuedict[cue])
                # cg3/cg4
                if cuedict[cue]['device'] in ('CG3', 'CG4'):
                    cue_verbose = f"{cuedict[cue]['device']}:   Cue {cuedict[cue]['cue_name']}"
                    cues_verbose_list.append(cue_verbose)
                # pause/hold
                if cuedict[cue]['device'] == 'Pause':
                    cue_verbose = f"{cuedict[cue]['device']}:   {cuedict[cue]['time']} seconds."
                    cues_verbose_list.append(cue_verbose)
                # kipro
                if cuedict[cue]['device'] == 'Kipro':
                    if cuedict[cue]['start'] is True:
                        mode = 'Start'
                    if cuedict[cue]['start'] is False:
                        mode = 'Stop'
                    device_index = cuedict[cue]['kipro']
                    device_name = kipro_data[device_index]['name']
                    cue_verbose = f"{cuedict[cue]['device']}:   " \
                                  f"{mode} {device_name}"
                    cues_verbose_list.append(cue_verbose)
                # resi
                if cuedict[cue]['device'] == 'Resi':
                    cue_verbose = f"{cuedict[cue]['device']}:   {cuedict[cue]['name']}"
                    cues_verbose_list.append(cue_verbose)
                # reminder
                if cuedict[cue]['device'] == 'Reminder':
                    reminder_to_display = cuedict[cue]['reminder'][0:40]
                    cue_verbose = f"{cuedict[cue]['device']}:   {cuedict[cue]['minutes']}m, {cuedict[cue]['seconds']}s: " \
                                  f"{reminder_to_display}"
                    cues_verbose_list.append(cue_verbose)
                # rosstalk
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
            # iteration needs to be a string, for use in dict keys when converted from json
            iteration = str(iteration+1)
            logging.debug('Current iteration in cue_decoder is %s', iteration)
            # cg3/cg4
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
            # rosstalk
            if cuedict[iteration]['device'] == 'Rosstalk':
                ip = rosstalk_ip
                port = rosstalk_port
                if cuedict[iteration]['type'] == 'CC':
                    command = f"CC {cuedict[iteration]['bank']}:{cuedict[iteration]['CC']}"
                    logging.debug(f"Cueing rosstalk command {command}")
                    rosstalk(rosstalk_ip = ip, rosstalk_port = port, command=command)
            # kipro
            if cuedict[iteration]['device'] == 'Kipro':
                # start
                if cuedict[iteration]['start'] is True:
                    # single
                    if not cuedict[iteration]['kipro'] == 0:
                        kipro_number = cuedict[iteration]['kipro']
                        logging.debug('Starting single kipro. %s', kipro_data[kipro_number]['name'])
                        kipro.start_absolute(ip=kipro_data[kipro_number]['ip'],
                                             name=kipro_data[kipro_number]['name'],
                                             include_date=True)
                        # all
                    if cuedict[iteration]['kipro'] == 0:
                        logging.debug('Starting all kipros')
                        for start_iteration in range(1, len(kipro_data)):
                            ip = kipro_data[start_iteration]['ip']
                            name = kipro_data[start_iteration]['name']
                            kipro.start_absolute(ip=ip, name=name, include_date=True)
                logging.debug('cue_decoder: iteration before passed to stop section is %s', iteration)
                # stop
                if cuedict[iteration]['start'] is False:
                    # single
                    if not cuedict[iteration]['kipro'] == 0:
                        kipro_number = cuedict[iteration]['kipro']
                        logging.debug('Stopping single kipro. %s', kipro_data[kipro_number]['name'])
                        kipro.transport_stop(ip=kipro_data[kipro_number]['ip'])
                    # all
                    if cuedict[iteration]['kipro'] == 0:
                        logging.debug('stopping all kipros')
                        for stop_iteration in range(1, len(kipro_data)):
                            ip = kipro_data[stop_iteration]['ip']
                            kipro.transport_stop(ip=ip)
            if cuedict[iteration]['device'] == 'Resi':
                logging.debug('Received new Resi cue: %s', cuedict[iteration]['command'])
                rosstalk(rosstalk_ip=resi_ip, rosstalk_port=resi_port, command=cuedict[iteration]['command'])

            else:
                pass

    def reminder_decoder(*self, cuedict):
        logging.debug('Searching for reminders in cue %s', cuedict)
        for iteration, cue in enumerate(cuedict):
            if cuedict[cue]['device'] == 'Reminder':
                reminder = cuedict[cue]['reminder']
                minutes = cuedict[cue]['minutes']
                seconds = cuedict[cue]['seconds']
                total_time = (minutes*60) + seconds

                return reminder, total_time
        else:
            logging.debug('No reminders found in current cue')
            return None


