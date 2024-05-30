import json
import pprint
import threading
import time
import os
import json

import requests
import urllib3.exceptions
from logzero import logger
from typing import List, Dict, Union

from configs.settings import *

from AHDlive import AHDLive
from bem104 import BEM104
from aja_kumo import AJAKumo
from controlflex import Flex
from ez_outlet_2 import EZOutlet2
from kipro import KiPro
from midi import Midi
from pvp import PVP
from ross_scpa import ScpaViaIP2SL
from sheet_reader import ReadSheet
from rosstalk import rosstalk as rt
from pco_plan import PcoPlan
from general_networking import is_host_online
from propresenter import ProPresenter

import pprint


class CueHandler:
    def __init__(self, devices: List[dict]):
        """
        This class contains functionality for handling cues.

        :param devices: the deserialized devices file found in configs/devices.json
        """

        self.devices: List[dict] = devices

        # Search through devices and find all kipro devices. If any exist, add them to below list for use later.
        self.all_kipros = []
        for device in self.devices:
            if device['type'] == 'kipro' and not device['uuid'] == all_kipros_uuid:
                self.all_kipros.append(device)

    def verbose_decode_cues(self, cuelist: List[dict]) -> List[str]:
        """
        "decodes" a list of cues in human-readable format that should be presented to the user.

        :param cuelist: list of app cues in [{"uuid": "7c361c29-cd60-4d79-8baa-9a51f88b1a27", "playlist_uuid":
         "E7C765C0-412B-4083-A4EF-412AB486EB32", "cue_uuid": "4A9F4428-9A43-4D2A-AA5C-1779D9B78752",
         "cue_name": "Song2"}] format.

        :return: list of decoded cues in ['CG4: Cue Song2'] format.
        """

        cues_verbose_list = []
        if cuelist is not None:
            for cue in cuelist:
                device = self.get_device_from_uuid(uuid=cue['uuid'])
                if device is None:
                    logger.critical('devices file mismatch')

                if device['type'] == 'pvp':
                    cue_verbose = f"{device['user_name']}: "
                    if cue['cue_type'] == 'cue_cue':
                        cue_name = PVP(device['ip_address'], port=device['port']).cue_name_from_uuids(playlist_uuid=cue['playlist_uuid'], cue_uuid=cue['cue_uuid'])
                        if type(cue_name) is None:
                            cue_verbose += '[cue removed]'
                        else:
                            cue_verbose += cue_name


                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'pause':
                    cue_verbose = f"{cue['device']}: {cue['time']} seconds"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'kipro':
                    if cue['start'] is True:
                        mode = 'Start'
                    else:
                        mode = 'Stop'
                    cue_verbose = f"KiPro:   " \
                                  f"{mode} {cue['name']}"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'resi':
                    cue_verbose = f"{device['user_name']}:   {cue['name']}"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'reminder':
                    reminder_to_display = cue['reminder'][0:40]
                    cue_verbose = f"{device['user_name']}:   {cue['minutes']}m, {cue['seconds']}s: " \
                                  f"{reminder_to_display}"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'ross_carbonite':
                    if cue['type'] == 'CC':
                        if device['cc_labels'] is not None:
                            # get spreadsheet file name from devices.json, convert it to dict with ReadSheet
                            cc_labels = ReadSheet(device['cc_labels']).read_cc_sheet()
                        else:
                            cc_labels = None
                            # get cc name from sheet[bank#][cc#]
                        cc_label = cc_labels['bank' + str(cue['bank'])][int(cue['CC'])-1]
                        cue_verbose = f"{device['user_name']}:" \
                                      f"   {cue['type']}:{cue['bank']}:{cue['CC']}:  {cc_label}"
                        cues_verbose_list.append(cue_verbose)

                if device['type'] == 'ez_outlet_2':
                    cue_verbose = f"{device['user_name']}: {cue['action']}"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'nk_scpa_ip2sl':
                    labels = ReadSheet(device['nk_labels']).read_lbl_file()
                    inputs = labels['inputs']
                    outputs = labels['outputs']
                    cue_verbose = f"{device['user_name']}: route input {cue['input']} " \
                                  f"({inputs[int(cue['input']-1)]}) to output " \
                                  f"{cue['output']} ({outputs[int(cue['output']-1)]})"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'bem104':
                    commands = {
                        'switch_off': 'Switch OFF',
                        'switch_on': 'Switch ON',
                        'toggle': 'Toggle State',
                        'pulse_on': 'Pulse off/on/off',
                        'pulse_off': 'Pulse on/off/on',
                        'pulse_toggle': 'Pulse Toggle'
                    }

                    cue_verbose = f"{device['user_name']}: Relay {cue['relay']}: {commands[cue['command']]}"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'controlflex':
                    cue_verbose = f"{device['user_name']}: {cue['zone']['friendly_name']}: "

                    if cue['zone']['zone_type'] == 'sony_pro_bravia':  # if cue is for a sony pro bravia
                        if cue['command']['args'] == 'power':  # cue is power
                            if int(cue['command']['value']) == 1:  # power on
                                cue_verbose += 'Power ON'
                            if int(cue['command']['value']) == 0:  # power off
                                cue_verbose += 'Power OFF'
                        if cue['command']['args'] == 'volume':  # cue is volume
                            cue_verbose += f'Set volume to {cue["command"]["value"]}%'
                        if cue['command']['args'] == 'input':  # cue is input
                            cue_verbose += f'Set to input {cue["command"]["value"]}'

                    if cue['zone']['zone_type'] == 'qsys':  # cue is for qsys
                        if cue['command']['args'] == 'mute':  # cue is to mute
                            if int(cue['command']['value']) == 1:
                                cue_verbose += f'MUTE {cue["zone"]["friendly_name"]}'
                            if int(cue['command']['value']) == 0:
                                cue_verbose += f'UNMUTE {cue["zone"]["friendly_name"]}'
                        if cue['command']['args'] == 'gain':  # cue is gain
                            cue_verbose += f'Set {cue["zone"]["friendly_name"]} to {cue["command"]["value"]}%'
                        if cue['command']['args'] == 'source':  # cue is change source
                            cue_verbose += f'Set {cue["zone"]["friendly_name"]} to' \
                                           f' {cue["zone"]["friendly_input_names"][cue["command"]["value"]-1]}'

                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'midi':
                    clear_commands = ['All',
                                      'Slide',
                                      'Background',
                                      'Props',
                                      'Messages',
                                      'Audio',
                                      'Bail to Logo']

                    video_controls = ['Go to Beginning',
                                      'Play/Pause',
                                      'Play',
                                      'Pause']

                    presentation_actions = ['Next Playlist Item',
                                            'Prev Playlist Item',
                                            'Next Slide',
                                            'Previous Slide',
                                            'Start Timeline',
                                            'Stop Timeline',
                                            'Rewind Timeline']

                    index_actions = ['Select Playlist',
                                     'Select Playlist Item',
                                     'Trigger Slide',
                                     'Select Media Playlist',
                                     'Trigger Media',
                                     'Select Audio Playlist',
                                     'Trigger Audio',
                                     'Toggle Prop On/Off',
                                     'Trigger Macro',
                                     'Start Timer',
                                     'Stop Timer',
                                     'Reset Timer']

                    cue_verbose = f'{device["user_name"]}: '
                    if device['midi_type'] == 'ProPresenter':
                        if not cue['command'] == 'custom':
                            if cue['command'] in clear_commands:
                                cue_verbose += 'Clear ' + cue['command']
                            if cue['command'] in video_controls:
                                cue_verbose += 'Video: ' + cue['command']
                            if cue['command'] in presentation_actions:
                                cue_verbose += cue['command']
                            if cue['command'] in index_actions:
                                cue_verbose += cue['command'] + ' ' + str(cue['index'])
                        elif cue['command'] == 'custom':
                            cue_verbose += f'Custom MIDI: Channel {cue["channel"]}, ' \
                                           f'Note {cue["note"]}, Velocity {cue["velocity"]}'

                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'aja_kumo':
                    kumo_api = AJAKumo(ip=device['ip_address'])

                    input_name = kumo_api.get_source_name(source_num=cue['input'])
                    output_name = kumo_api.get_dest_name(dest_num=cue['output'])

                    cue_verbose = ''
                    if input_name is not None and output_name is not None:
                        cue_verbose = f'{device["user_name"]}: route ' \
                                      f'{input_name} (ip{cue["input"]}) to {output_name} (op{cue["output"]})'
                    if input_name is None:
                        cue_verbose = f'{device["user_name"]}: route Input {cue["input"]} ' \
                                      f'to {output_name} (op{cue["output"]})'
                    if output_name is None:
                        cue_verbose = f'{device["user_name"]}: route {input_name} (ip{cue["input"]}) ' \
                                      f'to Output {cue["output"]})'
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'ah_dlive':
                    cue_verbose = f"{device['user_name']}: Go to Scene {cue['scene_number']}"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'obs':
                    cue_verbose = ''
                    if cue['command'] == 'start_recording':
                        cue_verbose = f"{device['user_name']}: Start Recording"
                    if cue['command'] == 'stop_recording':
                        cue_verbose = f"{device['user_name']}: Stop Recording"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'propresenter':
                    cue_verbose = ''
                    pp = ProPresenter(ip=device['ip_address'],port=device['port'])

                    # if device is offline, don't continue to next bit
                    if not pp.is_online():
                        cue_verbose = f"{device['user_name']}:"
                        cues_verbose_list.append(cue_verbose)
                        continue

                    if cue['command_type'] == 'trigger_macro':
                        does_exist = pp.does_macro_exist(cue['macro_uuid'])
                        if not does_exist:
                            propresenter_macro_name = '[Deleted Macro]'
                        else:
                            propresenter_macro_name = pp.get_macro_details_from_uuid(cue['macro_uuid'])['id']['name']
                        cue_verbose = f"{device['user_name']}: Cue Macro {propresenter_macro_name}"
                    cues_verbose_list.append(cue_verbose)

            return cues_verbose_list
        else:
            logger.debug(f'{__class__.__name__}.{self.verbose_decode_cues.__name__}: returning empty cuelist')
            return []

    def activate_cues(self, cuelist: List[dict]) -> None:
        """
        Cues actions in supplied cuelist.

        :param cuelist: list of app cues in [{"uuid": "7c361c29-cd60-4d79-8baa-9a51f88b1a27", "playlist_uuid":
         "E7C765C0-412B-4083-A4EF-412AB486EB32", "cue_uuid": "4A9F4428-9A43-4D2A-AA5C-1779D9B78752",
         "cue_name": "Song2"}] format.
        :return: None
        """

        for cue in cuelist:
            for device in self.devices:
                if cue['uuid'] == device['uuid']:
                    if device['type'] == 'pvp':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : pvp : {device["ip_address"]}:{device["port"]}')

                        PVP(device['ip_address'],
                            device['port']).cue_clip(playlist=cue['playlist_uuid'],
                                                     cue=cue['cue_uuid'])

                    elif device['type'] == 'ross_carbonite':
                        if cue['type'] == 'CC':
                            command = f"CC {cue['bank']}:{cue['CC']}"
                            logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : carbonite : {command} : {device["ip_address"]} : {device["port"]}')

                            rt(rosstalk_ip=device['ip_address'], rosstalk_port=device['port'], command=command)

                    elif device['type'] == 'kipro':
                        if device['uuid'] == '07af78bf-9149-4a12-80fc-0fa61abc0a5c':
                            logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : all kipros : start')

                            if cue['start']:
                                for kipro in self.all_kipros:
                                    KiPro().start_absolute(ip=kipro['ip_address'], name=kipro['user_name'])
                            if not cue['start']:
                                for kipro in self.all_kipros:
                                    KiPro().transport_stop(ip=kipro['ip_address'])
                        else:
                            if cue['start']:
                                logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} kipro : start={cue["start"]} : {device["ip_address"]}')

                                KiPro().start_absolute(ip=device['ip_address'], name=device['user_name'])
                            if not cue['start']:
                                KiPro().transport_stop(ip=device['ip_address'])

                    elif device['type'] == 'resi':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : resi : {cue["command"]} : {device["ip_address"]}')

                        rt(rosstalk_ip=device['ip_address'], rosstalk_port=device['port'], command=cue['command'])

                    elif device['type'] == 'pause':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : pause : {cue["time"]} seconds')
                        time.sleep(cue['time'])

                    elif device['type'] == 'ez_outlet_2':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : ezoutlet2 : {cue["action"]} : {device["ip_address"]}')

                        outlet = EZOutlet2(ip=device['ip_address'], user=device['username'],
                                           password=device['password'])
                        if cue['action'] == 'turn_off':
                            outlet.turn_off()
                        if cue['action'] == 'turn_on':
                            outlet.turn_on()
                        if cue['action'] == 'toggle_state':
                            outlet.toggle_state()
                        if cue['action'] == 'reset':
                            outlet.reset()

                    elif device['type'] == 'nk_scpa_ip2sl':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : scpaviaip2sl : route input {cue["input"]} to output {cue["output"]} : {device["ip_address"]}')

                        ScpaViaIP2SL(ip=device['ip_address']).switch_output(input=cue['input'],
                                                                            output=cue['output'])

                    elif device['type'] == 'bem104':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__}: bem104 : {cue["command"]} : {device["ip_address"]}')

                        b = BEM104(ip=device['ip_address'])

                        if cue['command'] == 'switch_off':
                            b.switch_off(relay=cue['relay'])
                        if cue['command'] == 'switch_on':
                            b.switch_on(relay=cue['relay'])
                        if cue['command'] == 'toggle':
                            b.toggle(relay=cue['relay'])
                        if cue['command'] == 'pulse_on':
                            b.pulse_on(relay=cue['relay'])
                        if cue['command'] == 'pulse_off':
                            b.pulse_off(relay=cue['relay'])
                        if cue['command'] == 'pulse_toggle':
                            b.pulse_toggle(relay=cue['relay'])

                    elif device['type'] == 'controlflex':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : controlflex : zone {cue["zone"]}')
                        flex = Flex(controlflex_ip=device['ip_address'])
                        if cue['zone']['zone_type'] == 'sony_pro_bravia':  # if cue is for a sony pro bravia
                            if cue['command']['args'] == 'power':  # cue is power
                                flex.sony_pro_bravia_power(device_name=cue['zone']['flex_name'],
                                                           state=int(cue['command']['value']))
                            if cue['command']['args'] == 'volume':  # cue is volume
                                flex.sony_pro_bravia_volume(device_name=cue['zone']['flex_name'],
                                                            volume_percent=int(cue['command']['value']))
                            if cue['command']['args'] == 'input':  # cue is input
                                flex.sony_pro_bravia_input(device_name=cue['zone']['flex_name'],
                                                           input_number=int(cue['command']['value']))
                        if cue['zone']['zone_type'] == 'qsys':  # if cue is qsys
                            if cue['command']['args'] == 'mute':  # cue is mute
                                flex.qsys_mute(qsys_name=cue['zone']['qsys_name'],
                                               qsys_zone=cue['zone']['control_id'],
                                               state=cue['command']['value'])
                            if cue['command']['args'] == 'gain':  # cue is gain
                                flex.set_qsys_volume_percent(qsys_name=cue['zone']['qsys_name'],
                                                             qsys_zone=cue['zone']['control_id'],
                                                             percent=cue['command']['value'])
                            if cue['command']['args'] == 'source':  # cue is source
                                flex.qsys_source(qsys_name=cue['zone']['qsys_name'],
                                                 qsys_zone=cue['zone']['control_id'],
                                                 source_number=cue['command']['value'])

                    elif device['type'] == 'aja_kumo':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : aja kumo : route input {cue["input"]} to output {cue["output"]}: {device["ip_address"]}')

                        AJAKumo(ip=device['ip_address']).route_source_to_dest(source_num=cue['input'],
                                                                              dest_num=cue['output'])

                    elif device['type'] == 'ah_dlive':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : ah_dlive : goto scene {cue["scene_number"]} : {device["ip_address"]}')

                        AHDLive(ip_address=device['ip_address']).recall_scene(int(cue['scene_number']))

                    elif device['type'] == 'midi':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : midi')

                        midi = Midi()
                        midi_port_index = midi.get_midi_out().index(device['midi_device'])
                        midi.set_out_port(midi_port_index)

                        channel = 0
                        note = 0
                        velocity = 1

                        if device['midi_type'] == 'ProPresenter':
                            if not cue['command'] == 'custom':

                                # dict of built-in commands & their default midi notes
                                default_commands = {
                                    'All': 0,
                                    'Slide': 1,
                                    'Background': 2,
                                    'Props': 3,
                                    'Messages': 28,
                                    'Audio': 4,
                                    'Bail to Logo': 5,
                                    'Go to Beginning': 6,
                                    'Play/Pause': 7,
                                    'Play': 8,
                                    'Pause': 9,
                                    'Next Playlist Item': 10,
                                    'Prev Playlist Item': 11,
                                    'Next Slide': 12,
                                    'Previous Slide': 13,
                                    'Start Timeline': 14,
                                    'Stop Timeline': 15,
                                    'Rewind Timeline': 16,
                                    'Select Playlist': 17,
                                    'Select Playlist Item': 18,
                                    'Trigger Slide': 19,
                                    'Select Media Playlist': 20,
                                    'Trigger Media': 21,
                                    'Select Audio Playlist': 22,
                                    'Trigger Audio': 23,
                                    'Toggle Prop On/Off': 24,
                                    'Trigger Macro': 29,
                                    'Start Timer': 25,
                                    'Stop Timer': 26,
                                    'Reset Timer': 27
                                }

                                note = default_commands[cue['command']]
                                if 'index' in cue.keys():  # cue type is propresenter preset with custom index
                                    logger.debug('cue_creator.activate_cues: midi: Midi command is %s, with index '
                                                 '%s', cue['command'], cue['index'])
                                    velocity = cue['index']

                            if cue['command'] == 'custom':  # cue type is propresenter custom midi
                                logger.debug('cue_creator.activate_cues: midi: Midi type is propresenter custom')
                                channel = cue['channel']
                                note = cue['note']
                                velocity = cue['velocity']

                        if device['midi_type'] == 'Other/Custom':  # cue type is custom midi
                            logger.debug('cue_creator.activate_cues: midi: Midi type is custom. Channel: '
                                         '%s, note: %s, velocity: %s', cue['channel'], cue['note'], cue['velocity'])
                            channel = cue['channel']
                            note = cue['note']
                            velocity = cue['velocity']

                        midi.send_noteon(channel=channel, note=note, velocity=velocity)

                    elif device['type'] == 'obs':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : OBS : {cue["command"]} : {device["ip_address"]}')
                        requests.post(f"http://{device['ip_address']}:8707/{cue['command']}")

                    elif device['type'] == 'propresenter':
                        logger.debug(f'{__class__.__name__}.{self.activate_cues.__name__} : Propresenter : {cue["command_type"]} : {device["ip_address"]}:{device["port"]}')

                        pp = ProPresenter(ip=device['ip_address'], port=device['port'])
                        if cue['command_type'] == 'trigger_macro':
                            pp.cue_macro(cue['macro_uuid'])

                    elif device['uuid'] == reminder_uuid:
                        pass

                    else:
                        logger.warning('Received cue not in activate_cues list: %s', cue)
                        pass


    @staticmethod
    def update_october_2022_cue(cuelist: list) -> dict:
        """
        Converts an old cuelist in the old pre-October 2022 style to the new post-October 2022 style.

        PRE OCTOBER 2022 EXAMPLE:
        [{"uuid": "7c361c29-cd60-4d79-8baa-9a51f88b1a27", "playlist_uuid": "E7C765C0-412B-4083-A4EF-412AB486EB32",
        "cue_uuid": "4A9F4428-9A43-4D2A-AA5C-1779D9B78752", "cue_name": "Song2"}]
        Notice that it's a list, not a dictionary. This provides very limited functionality for cues that are not action
        cues, like advance to next, for example.

        POST OCTOBER 2022 EXAMPLE:
        {"action_cues": [{"uuid": "0763d390-aa2d-4802-ac81-cef1787abda3", "playlist_uuid":
        "4BF4ABCA-15E9-4EE3-BA36-5EF722877482", "cue_uuid": "3156E7B2-59C4-4A62-9152-33E672409DB0",
        "cue_name": "Preroll"}], "advance_to_next_on_time": [], "advance_to_next_automatically": false}
        This is a dictionary that contains keys such as action_cues, advance_to_next_on_time, and
        advance_to_next_automatically, with easy additions in the future.
        advance_to_next_on_time and advance_to_next_automatically will output as false from this method.

        :param cuelist: the list of cues to convert.
        :return: The converted dict
        """

        cue_dict = {
            'action_cues': cuelist,
            'advance_to_next_on_time': [],
            'advance_to_next_automatically': False
        }

        # if it's the old advance to next on time uuid, add times to correct dict key
        for iteration, cue in enumerate(cuelist):
            if cue['uuid'] == 'a0fac1cd-3bff-4286-80e2-20b284361ba0':
                for _time in cue['times']:
                    cue_dict['advance_to_next_on_time'].append(_time)
                cuelist.pop(iteration)

        return cue_dict

    @staticmethod
    def check_and_update_plan_for_october_2022_cues(service_type_id: int, service_id: int):
        """
        See update_october_2022_cue for more documentation.
        This will search through plan item cues on a plan and if they're in pre-october 2022 format, it will
        fix & update them.

        :param service_type_id: the service type id that the plan lives in.
        :param service_id: service id that contains the cues that need to be inspected and fixed.
        :return:
        """
        logger.debug('Checking to see if app cues need to be updated on service type id %s, service id %s',
                     service_type_id, service_id)

        pco = PcoPlan(service_type=service_type_id, plan_id=service_id)
        plan_items = pco.get_plan_items()

        for plan_item in plan_items:
            if 'App Cues' in plan_item['notes']:
                if type(plan_item['notes']['App Cues']) == list:
                    logger.info('Found app cue to update on item: %s', plan_item['title'])

                    updated_item = CueHandler.update_october_2022_cue(cuelist=plan_item['notes']['App Cues'])
                    pco.create_and_update_item_app_cue(item_id=plan_item['id'], app_cue=json.dumps(updated_item))

    def get_device_from_uuid(self, uuid: str) -> dict:
        """
        Searches through devices dict for specific uuid & returns device that corresponds with uuid

        :param uuid: the uuid of the device to retrieve data from
        :return: device that corresponds with supplied uuid. Returns empty dict if not found.
        """

        for device in self.devices:
            if device['uuid'] == uuid:
                return device

        logger.info('did not find device from uuid %s', uuid)
        return {}

    def cues_are_valid(self, cuelist: List[dict]) -> List[Dict[bool, Union[str, None]]]:
        """
        Check if a device is offline, or there are any old or invalid cues on an item, for example,
         if there's a cue to play a PVP video, but that cue no longer exists on the pvp machine.
        :param cuelist: list of cues to test
        :return: List of dict of bool: reason of failure that should be made user-visible. For example,
        [True: None,
        False: "device offline",
        True: None,
        True: None,
        False: "cue not found"]
        """

        output: List[Dict[bool, Union[str, None]]] = []

        # devices to run a "ping" check on
        ip_devices: List[str] = ['resi',
                                 'nk_scpa_ip2sl',
                                 'ross_carbonite',
                                 'kipro',
                                 'ez_outlet_2',
                                 'bem104',
                                 'controlflex',
                                 'aja_kumo',
                                 'ah_dlive',
                                 'pvp',
                                 'obs',
                                 'propresenter']

        for i, cue in enumerate(cuelist):
            output.append({True: None})

            cue_uuid = cue['uuid']
            cue_device = self.get_device_from_uuid(cue_uuid)

            # ping check
            if cue_device['type'] in ip_devices and cue_device['user_name'] != 'All Kipros':
                if not is_host_online(cue_device['ip_address']):
                    logger.warning(f'{__class__.__name__}.{self.cues_are_valid.__name__}: ping to device {cue_device["ip_address"]} failed.')
                    output[i] = {False: f'Device Offline ({cue_device["ip_address"]})'}
                    continue

            # uuid check on pvp cue
            if cue_device['type'] == 'pvp':
                pvp_init = PVP(ip=cue_device['ip_address'], port=cue_device['port'])
                if not pvp_init.does_cue_exist(playlist_uuid=cue['playlist_uuid'], cue_uuid=cue['cue_uuid']):
                    logger.warning(f'{__class__.__name__}.{self.cues_are_valid.__name__}: PVP cue invalid')
                    output[i] = {False: 'PVP cue does not exist on the target machine. Delete & Re-add it.'}
                    continue

            # see if obs script is running
            if cue_device['type'] == 'obs':
                try:
                    r = requests.get(f"http://{cue_device['ip_address']}:8707/online_check", timeout=.5)
                except:  # plugin not running but computer online
                    logger.warning(f'{__class__.__name__}.{self.cues_are_valid.__name__}: OBS plugin not running at {cue_device["ip_address"]}.')
                    output[i] = {False: f'OBS plugin not running or OBS not open: ({cue_device["ip_address"]})'}
                    continue
                if r.text != 'True' or r.status_code != 200:  # problem with plugin or obs not initialized
                    logger.warning(f'{__class__.__name__}.{self.cues_are_valid.__name__}: OBS plugin error {cue_device["ip_address"]}.')
                    output[i] = {False: f'OBS plugin error!: ({cue_device["ip_address"]})'}
                    continue

            # see if propresenter cues are valid
            if cue_device['type'] == 'propresenter':
                pp = ProPresenter(ip=cue_device['ip_address'], port=cue_device['port'])

                if not pp.is_online():
                    output[i] = {False: 'Propresenter offline! Check network connection or propresenter config.'}
                    logger.warning(f'{__class__.__name__}.{self.cues_are_valid.__name__} : Propresenter offline. {cue_device["ip_address"]}:{cue_device["port"]}')
                    continue
                if cue['command_type'] == 'trigger_macro':
                    if not pp.does_macro_exist(cue['macro_uuid']):
                        logger.info(f'{__class__.__name__}.{self.cues_are_valid.__name__} : Propresenter macro does not exist. {cue_device["ip_address"]}:{cue_device["port"]}')
                        output[i] = {False: 'ProPresenter Macro does not exist!'}
                        continue

        return output


if __name__ == '__main__':
    with open(os.path.join('configs', 'devices.json'), 'r') as f:
        devices = json.loads(f.read())
    ch = CueHandler(devices=devices)

    cues_str = '[{"uuid": "7f64e879-849e-4427-90f5-e6d403065b5a", "command_type": "trigger_macro", "macro_uuid": "1ACF8D8C-14CB-4122-AD17-77F95FA7C06B"}, {"uuid": "e04a9555-b090-4a5c-a220-7855197aea8e", "command": {"args": "source", "value": 1}, "zone": {"zone_type": "qsys", "qsys_name": "A_QSys", "qsys_zone_type": "qsys_source", "control_id": "LobbySource", "friendly_name": "Lobby Source", "friendly_input_names": ["Live Feed", "Spotify"]}}, {"uuid": "e04a9555-b090-4a5c-a220-7855197aea8e", "command": {"args": "gain", "value": "78"}, "zone": {"zone_type": "qsys", "qsys_name": "A_QSys", "qsys_zone_type": "qsys_gain", "control_id": "LobbyGain", "friendly_name": "Lobby Gain"}}, {"uuid": "e04a9555-b090-4a5c-a220-7855197aea8e", "command": {"args": "power", "value": "1"}, "zone": {"zone_type": "sony_pro_bravia", "flex_name": "D_Office", "friendly_name": "Creative Suite"}}, {"uuid": "e04a9555-b090-4a5c-a220-7855197aea8e", "command": {"args": "volume", "value": "80"}, "zone": {"zone_type": "sony_pro_bravia", "flex_name": "D_Office", "friendly_name": "Creative Suite"}}, {"uuid": "b652b57e-c426-4f83-87f3-a7c4026ec1f0", "device": "reminder", "minutes": 0, "seconds": 0, "reminder": "Start 30m countdown"}, {"uuid": "7c361c29-cd60-4d79-8baa-9a51f88b1a27", "playlist_uuid": "E7C765C0-412B-4083-A4EF-412AB486EB32", "cue_uuid": "7FE08046-40A0-4DD4-A52F-2BBC7BAE47E2", "cue_name": "message"}, {"uuid": "d75d1ed3-619e-4b20-84e0-ba0f62c67e67", "type": "CC", "bank": 2, "CC": 1}, {"uuid": "d75d1ed3-619e-4b20-84e0-ba0f62c67e67", "type": "CC", "bank": 2, "CC": 32}, {"uuid": "d75d1ed3-619e-4b20-84e0-ba0f62c67e67", "type": "CC", "bank": 2, "CC": 12}]'

    cues_decoded = json.loads(cues_str)
    # pprint.pprint(cues_decoded)

    # pprint.pprint(ch.verbose_decode_cues(cuelist=json.loads(cues_str)))
    pprint.pprint(ch.cues_are_valid(cues_decoded))