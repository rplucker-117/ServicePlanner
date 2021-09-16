import requests
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import json
from settings import *
import pprint
from logzero import logger
import datetime
from pvp import pvp
from pco_plan import PcoPlan
from tkinter import ttk
from rosstalk import rosstalk as rt
from kipro import *
import threading
from sheet_reader import ReadSheet
import math
from ez_outlet_2 import EZOutlet2
from select_service import SelectService
from exos_telnet import Exos
import socket
from tkinter import messagebox
from ross_scpa import ScpaViaIP2SL
from sheet_reader import ReadSheet
from bem104 import BEM104
from controlflex import Flex
import uuid
from aja_kumo import AJAKumo

class CueCreator:
    def __init__(self, startup, ui, cue_type='item', devices=None, imported_cues=None):

        self.service_type_id = startup.service_type_id
        self.plan_id = startup.service_id
        self.cue_type = cue_type

        self.startup = startup

        self.pco_plan = PcoPlan(service_type=self.service_type_id, plan_id=self.plan_id)

        self.main_ui = ui

        self.cue_creator_window = Tk()
        self.cue_creator_window.withdraw()
        self.cue_creator_window.configure(bg=bg_color)

        # Main item frames
        self.current_cues_frame = Frame(self.cue_creator_window, bg=bg_color, width=600, height=300)  # top left
        self.cue_type_buttons_frame = Frame(self.cue_creator_window, bg=bg_color)  # Holds buttons for adding cues on right side
        self.bottom_frame = Frame(self.cue_creator_window, bg=bg_color)  # very bottom, holds separator as well as main function buttons
        self.bottom_buttons_frame = Frame(self.bottom_frame, bg=bg_color)  # holds add/cancel/test buttons at bottom. Child of bottom_frame
        self.advance_to_next_frame = Frame(self.cue_creator_window, bg=bg_color)

        self.devices_buttons_frame = Frame(self.cue_type_buttons_frame, bg=bg_color)
        self.cue_presets_button_frame = Frame(self.cue_type_buttons_frame, bg=bg_color)

        self.current_cues_listbox = Listbox(self.current_cues_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-1), height=15)

        # elements for is type is 'plan' cue
        self.custom_name_frame = Frame(self.bottom_frame, bg=bg_color)
        self.custom_name_entry = Entry(self.custom_name_frame, width=40, bg=text_entry_box_bg_color, fg=text_color, font=(font, plan_text_size))

        self.input_item_id = None
        self.input_item = None
        self.cues_display_text = str()
        self.current_cues = []

        self.devices = devices

        self.all_kipros = []

        self.includes_kipro = False

        # advance to next
        self.advance_to_next_labels = []
        self.advance_to_next_remove_buttons = []

        for device in self.devices:
            if device['type'] == 'kipro' and device['user_name'] != 'All Kipros':
                self.includes_kipro = True

        if self.devices is not None:
            for device in self.devices:
                if device['type'] == 'kipro' and not device['uuid'] == '07af78bf-9149-4a12-80fc-0fa61abc0a5c':
                    self.all_kipros.append(device)

        if self.cue_type == 'plan':
            self.imported_cues = self.pco_plan.get_plan_app_cues()
            if self.imported_cues is None:
                self.imported_cues = []

        def verify_ip(ip):
            try:
                socket.inet_aton(ip)
                return True
            except socket.error:
                return False

        def is_open(ip, port):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            try:
                s.connect((ip, int(port)))
                s.shutdown(1)
                return True
            except:
                return False

        # obtain resi ip address automatically
        if cue_type == 'plan':
            for device in self.devices:
                if device['type'] == 'resi' and device['obtain_ip_automatically']:
                    logger.debug('cue_creator: attempting to obtain resi ip automatically')
                    try:
                        ip = Exos(host=device['exos_mgmt_ip'],
                                  user=device['exos_mgmt_user'],
                                  password=device['exos_mgmt_pass']).get_port_addresses(device['resi_exos_port'])['ips'][0]
                        if ip != device['ip_address']:
                            logger.warning('Resi ip mismatch: devices file: %s, exos: %s', device['ip_address'], ip)
                            messagebox.showinfo(title='IP address mismatch', message=f"Resi ip acquired from exos switch is different from the ip in device file. Using updated ip {ip} instead of file {device['ip_address']}. \n\n"
                                                                                     "It's safe to proceed with your live show if you suspect this is correct and you TEST IT, but updating your devices file with the updated address in the future is encouraged.")
                    except TimeoutError:
                        ip = device['ip_address']
                        pass

                    if verify_ip(ip) and is_open(ip=ip, port=7788): # if ip acquired from exos is valid and port 7788 is open, proceed with using acquired address. Else, use ip on file
                        logger.debug('cue_creator: successfully got resi ip: %s', ip)
                        device['ip_address'] = ip
                    else:
                        messagebox.showerror(title='Could not get resi ip', message=f'Could not automatically get Resi Decoder IP address. Using default {device["ip_address"]} instead.')
                        logger.error('cue_creator: did not successfully get resi address. using default %s instead.', device['ip_address'])

    def create_cues(self, input_item=None):
        self.input_item = input_item
        try:
            if 'App Cues' in input_item['notes']:
                yes_no = messagebox.askyesno('Overwrite existing cues', message="There's existing cues on this item. Do you want to overwrite them?")
                if yes_no: # User chose to delete existing cues
                    logger.debug('create_cues: Overwriting existing cues')
                    self.__open_cue_creator(overwrite=True)
                if not yes_no: # User chose to append onto existing cues
                    self.__open_cue_creator(overwrite=False)
            else: # No cues exist
                self.__open_cue_creator(overwrite=None)
        except TypeError:
            self.__open_cue_creator(overwrite=None)


        # input_item_id is None if setting a plan cue
        try:
            self.input_item_id = input_item['id']
        except TypeError:
            logger.debug('CueCreator.create_cues: Creating plan cue, no input item')

    def verbose_decode_cues(self, cuelist):
        cues_verbose_list = []
        if cuelist is not None:
            for cue in cuelist:
                logger.debug('creating verbose output from %s', cue)
                device = self.__get_device_user_name_from_uuid(uuid=cue['uuid'])
                if device is None:
                    logger.critical('devices file mismatch')

                if device['type'] == 'pvp':
                    cue_verbose = f"{device['user_name']}:   Cue {cue['cue_name']}"
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
                            cc_labels = ReadSheet(device['cc_labels']).read_cc_sheet() # get spreadsheet file name from devices.json, convert it to dict with ReadSheet
                        else:
                            cc_labels = None
                        cc_label = cc_labels['bank' + str(cue['bank'])][int(cue['CC'])-1] # get cc name from sheet[bank#][cc#]
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
                    cue_verbose = f"{device['user_name']}: route input {cue['input']} ({inputs[int(cue['input']-1)]}) to output {cue['output']} ({outputs[int(cue['output']-1)]})"
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

                    if cue['zone']['zone_type'] == 'sony_pro_bravia': #if cue is for a sony pro bravia
                        if cue['command']['args'] == 'power': # cue is power
                            if int(cue['command']['value']) == 1: # power on
                                cue_verbose += 'Power ON'
                            if int(cue['command']['value']) == 0: # power off
                                cue_verbose += 'Power OFF'
                        if cue['command']['args'] == 'volume': # cue is volume
                            cue_verbose += f'Set volume to {cue["command"]["value"]}%'
                        if cue['command']['args'] == 'input': # cue is input
                            cue_verbose += f'Set to input {cue["command"]["value"]}'

                    if cue['zone']['zone_type'] == 'qsys': # cue is for qsys
                        if cue['command']['args'] == 'mute': #cue is to mute
                            if int(cue['command']['value']) == 1:
                                cue_verbose += f'MUTE {cue["zone"]["friendly_name"]}'
                            if int(cue['command']['value']) == 0:
                                cue_verbose += f'UNMUTE {cue["zone"]["friendly_name"]}'
                        if cue['command']['args'] == 'gain': #cue is gain
                            cue_verbose += f'Set {cue["zone"]["friendly_name"]} to {cue["command"]["value"]}%'
                        if cue['command']['args'] == 'source': # cue is change source
                            cue_verbose += f'Set {cue["zone"]["friendly_name"]} to {cue["zone"]["friendly_input_names"][cue["command"]["value"]-1]}'

                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'aja_kumo':
                    kumo_api = AJAKumo(ip=device['ip_address'])

                    input_name = kumo_api.get_source_name(source_num=cue['input'])
                    output_name = kumo_api.get_dest_name(dest_num=cue['output'])

                    if input_name is not None and output_name is not None:
                        cue_verbose = f'{device["user_name"]}: route {input_name} (ip{cue["input"]}) to {output_name} (op{cue["output"]})'
                    if input_name is None:
                        cue_verbose = f'{device["user_name"]}: route Input {cue["input"]} to {output_name} (op{cue["output"]})'
                    if output_name is None:
                        cue_verbose = f'{device["user_name"]}: route {input_name} (ip{cue["input"]}) to Output {cue["output"]})'
                    cues_verbose_list.append(cue_verbose)

            logger.debug('verbose_decode_cues: returning %s', cues_verbose_list)
            return cues_verbose_list

    def activate_cues(self, cues):
        logger.debug('activate_cues called, cues input: %s', cues)
        def start_cues():
            logger.debug('cue_creator.activate_cues.start_cues called')
            for cue in cues:
                for device in self.devices:
                    if cue['uuid'] == device['uuid']:
                        if device['type'] == 'pvp':
                            pvp(device['ip_address'], device['port']).cue_clip_via_uuid(playlist_uuid=cue['playlist_uuid'], cue_uuid=cue['cue_uuid'])

                        elif device['type'] == 'ross_carbonite':
                            if cue['type'] == 'CC':
                                command = f"CC {cue['bank']}:{cue['CC']}"
                                logger.info('activate_cues: cueing rosstalk: %s', command)
                                rt(rosstalk_ip=device['ip_address'], rosstalk_port=device['port'], command=command)

                        elif device['type'] == 'kipro':
                            if device['uuid'] == '07af78bf-9149-4a12-80fc-0fa61abc0a5c':
                                if cue['start']:
                                    for kipro in self.all_kipros:
                                        KiPro().start_absolute(ip=kipro['ip_address'], name=kipro['user_name'])
                                if not cue['start']:
                                    for kipro in self.all_kipros:
                                        KiPro().transport_stop(ip=kipro['ip_address'])
                            else:
                                if cue['start']:
                                    KiPro().start_absolute(ip=device['ip_address'], name=device['user_name'])
                                if not cue['start']:
                                    KiPro().transport_stop(ip=device['ip_address'])

                        elif device['type'] == 'resi':
                            rt(rosstalk_ip=device['ip_address'], rosstalk_port=device['port'], command=cue['command'])

                        elif device['type'] == 'pause':
                            logger.debug('Pausing %s seconds', cue['time'])
                            time.sleep(cue['time'])

                        elif device['type'] == 'ez_outlet_2':
                            outlet = EZOutlet2(ip=device['ip_address'], user=device['username'], password=device['password'])
                            if cue['action'] == 'turn_off':
                                outlet.turn_off()
                            if cue['action'] == 'turn_on':
                                outlet.turn_on()
                            if cue['action'] == 'toggle_state':
                                outlet.toggle_state()
                            if cue['action'] == 'reset':
                                outlet.reset()

                        elif device['type'] == 'nk_scpa_ip2sl':
                            ScpaViaIP2SL(ip=device['ip_address']).switch_output(input=cue['input'], output=cue['output'])

                        elif device['type'] == 'bem104':
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
                            flex = Flex(controlflex_ip=device['ip_address'])

                            if cue['zone']['zone_type'] == 'sony_pro_bravia':  # if cue is for a sony pro bravia
                                if cue['command']['args'] == 'power':  # cue is power
                                    flex.sony_pro_bravia_power(device_name=cue['zone']['flex_name'], state=int(cue['command']['value']))
                                if cue['command']['args'] == 'volume':  # cue is volume
                                    flex.sony_pro_bravia_volume(device_name=cue['zone']['flex_name'], volume_percent=int(cue['command']['value']))
                                if cue['command']['args'] == 'input':  # cue is input
                                    flex.sony_pro_bravia_input(device_name=cue['zone']['flex_name'], input_number=int(cue['command']['value']))
                            if cue['zone']['zone_type'] == 'qsys':  # if cue is qsys
                                if cue['command']['args'] == 'mute': # cue is mute
                                    flex.qsys_mute(qsys_name=cue['zone']['qsys_name'], qsys_zone=cue['zone']['control_id'], state=cue['command']['value'])
                                if cue['command']['args'] == 'gain': # cue is gain
                                    flex.set_qsys_volume_percent(qsys_name=cue['zone']['qsys_name'], qsys_zone=cue['zone']['control_id'], percent=cue['command']['value'])
                                if cue['command']['args'] == 'source':  # cue is source
                                    flex.qsys_source(qsys_name=cue['zone']['qsys_name'], qsys_zone=cue['zone']['control_id'], source_number=cue['command']['value'])

                        elif device['type'] == 'aja_kumo':
                            logger.debug('aja kumo: route input %s to output %s', cue['input'], cue['output'])
                            AJAKumo(ip=device['ip_address']).route_source_to_dest(source_num=cue['input'], dest_num=cue['output'])

                        else:
                            logger.warning('Received cue not in activate_cues list: %s', cue)
                            pass

        threading.Thread(target=start_cues).start()

    def __get_device_user_name_from_uuid(self, uuid):
        for device in self.devices:
            if device['uuid'] == uuid:
                return device

    def __open_cue_creator(self, overwrite=False):  # opens main cue creator window

        if overwrite is False:
            existing_cues = self.input_item['notes']['App Cues']
            for existing_cue in existing_cues:
                self.current_cues.append(existing_cue)

        self.cue_creator_window.deiconify()

        self.current_cues_frame.grid(row=0, column=0)
        self.cue_type_buttons_frame.grid(row=0, column=2)
        self.bottom_frame.grid(row=2, column=0)
        self.bottom_buttons_frame.grid(row=1, column=0)

        self.devices_buttons_frame.pack(side=LEFT) # this and cue_presets_button_frame go inside cue_type_buttons_frame
        self.cue_presets_button_frame.pack(side=RIGHT)



        # Current cues display
        self.current_cues_frame.pack_propagate(0)
        cues_to_add_label = Label(self.current_cues_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Cues to Add:')
        cues_to_add_label.pack(anchor='n')

        self.__update_cues_display()
        self.current_cues_listbox.pack(anchor='w', fill=BOTH, pady=10)

        self.cue_presets = None
        if os.path.exists('cue_presets.json'):
            try:
                with open('cue_presets.json', 'r') as f:
                    self.cue_presets = json.loads(f.read())
                    logger.debug('Read cue_presets.json. Contents: %s', self.cue_presets)
            except json.decoder.JSONDecodeError:
                logger.error('Unable to read json on cue_presets.json, continuing as None')

        if self.cue_type == 'item':
            try:
                cues_to_add_label.configure(text=f"Cues to add to {self.input_item['title']}:")
                logger.debug(f"cue_creator.__open_cue_creator: changed label to       {cues_to_add_label.cget('text')}")
            except Exception as e:
                logger.error(f"cue_creator.__open_cue_creator exception: {e}")

        # Separator frames
        Frame(self.bottom_frame, bg=separator_color, width=600, height=1).grid(row=0, column=0) # Above bottom buttons
        Frame(self.cue_creator_window, bg=separator_color, width=1, height=300).grid(row=0, column=1) # Left of cue type buttons

        # If plan/global cue, add custom name
        if self.cue_type in ('plan', 'global'):
            self.custom_name_frame.grid(row=0, column=0)
            Label(self.custom_name_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Cue Name').pack()
            self.custom_name_entry.pack()

        def add_cue_clicked(device):
            logger.debug('Add cue button clicked: %s, %s', device['user_name'], device['uuid'])

            if device['type'] == 'nk_scpa_ip2sl':
                self.__add_nk_scpa_ip2sl_cue(device)
            elif device['type'] == 'pvp':
                self.__add_pvp_cue(device)
            elif device['type'] == 'ross_carbonite':
                if 'cc_labels' in device.keys():
                    cc_labels = ReadSheet(device['cc_labels']).read_cc_sheet()
                else:
                    cc_labels = None
                self.__add_carbonite_cue(device, cc_labels=cc_labels)
            elif device['type'] == 'resi':
                self.__add_resi_cue(device)
            elif device['type'] == 'ez_outlet_2':
                self.__add_ez_outlet_2(device)
            elif device['type'] =='bem104':
                self.__add_bem104(device)
            elif device['type'] == 'controlflex':
                self.__add_controlflex(device)
            elif device['type'] == 'aja_kumo':
                self.__add_aja_kumo(device)

        if self.devices is not None: # if the device is not pause, reminder, or kipro, create a button for it
            for device in self.devices:
                if not device['type'] in ('pause', 'reminder', 'kipro', 'advance_on_time'):
                    button_name = 'Add ' + device['user_name'] + '(' + device['type'] + ')' + ' cue'
                    Button(self.devices_buttons_frame, text=button_name, font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=lambda device=device: add_cue_clicked(device)).pack(padx=10)
                elif device['type'] == 'kipro' and not device['user_name'] == 'All Kipros':
                    self.includes_kipro = True

        if self.includes_kipro:
            Button(self.devices_buttons_frame, text='Add Kipro Cue', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_kipro_cue).pack(padx=20)

        #pause/reminder buttons, goes in with other device cue buttons
        Button(self.devices_buttons_frame, text='Add Pause', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_pause_cue_clicked).pack(padx=20)
        Button(self.devices_buttons_frame, text='Add Reminder', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_reminder_cue_clicked).pack(padx=20)

        def add_preset_clicked(preset):
            logger.debug('Add preset button clicked: %s', preset)
            for cue in preset['cues']:
                self.current_cues.append(cue)
            self.__update_cues_display()

        if self.cue_presets is not None:
            for preset in self.cue_presets:
                Button(self.cue_presets_button_frame, text=preset['name'], font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=lambda preset=preset: add_preset_clicked(preset)).pack(padx=20)

        if self.cue_type == 'item':
            Button(self.bottom_buttons_frame, text='Schedule advance to next', font=(font, plan_text_size-1), bg=bg_color, fg=text_color, command=lambda: self.__add_advance_cue()).grid(row=1, column=5)

        # Bottom Buttons
        Button(self.bottom_buttons_frame, text='Test', font=(font, plan_text_size-1), bg=bg_color, fg=text_color, command=self.__test).grid(row=1, column=0)
        Button(self.bottom_buttons_frame, text='Add Cue(s)', font=(font, plan_text_size-1), bg=bg_color, fg=text_color, command=self.__add_cues).grid(row=1, column=1)
        Button(self.bottom_buttons_frame, text='Cancel', font=(font, plan_text_size-1), bg=bg_color, fg=text_color, command=lambda: self.cue_creator_window.destroy()).grid(row=1, column=2)
        Button(self.bottom_buttons_frame, text='Copy cues from a plan item', font=(font, plan_text_size-1), bg=bg_color, fg=text_color, command=lambda: self.__copy_from_plan_item()).grid(row=1, column=3)
        Button(self.bottom_buttons_frame, text='Remove Selected', font=(font, plan_text_size-1), bg=bg_color, fg=text_color, command=lambda: self.__remove_selected()).grid(row=1, column=4)
        Button(self.bottom_buttons_frame, text='Create Preset from Added Cues', font=(font, plan_text_size-1), bg=bg_color, fg=text_color, command=lambda: self.__create_preset()).grid(row=1, column=6)

        self.__update_cues_display()

    def __add_nk_scpa_ip2sl_cue(self, device):
        logger.debug('__add_nk_scpa_ip2sl_cue: received. device: %s', device)

        add_nk_cue = Tk()
        add_nk_cue.configure(bg=bg_color)

        has_labels = False

        if 'nk_labels' in device.keys():
            has_labels = True
            labels = ReadSheet(device['nk_labels']).read_lbl_file()
            input_labels = labels['inputs']
            output_labels = labels['outputs']

        total_inputs = device['inputs']
        total_outputs = device['outputs']

        #  inputs radiobuttons

        inputs_frame = Frame(add_nk_cue, bg=bg_color)
        inputs_buttons = []

        selected_input = IntVar(inputs_frame)

        for input in range(1, int(total_inputs) + 1):
            if has_labels:
                input_label = f"{str(input)}:  {input_labels[input-1]}"
            else:
                input_label = f"Input {str(input)}"

            inputs_buttons.append(Radiobutton(inputs_frame,
                                              bg=bg_color,
                                              selectcolor=bg_color,
                                              fg=text_color, font=(font, other_text_size-2),
                                              text=input_label,
                                              variable=selected_input,
                                              value=input))

        for iteration, button in enumerate(inputs_buttons):
            row = math.floor(iteration/6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        #  outputs radiobuttons

        outputs_frame = Frame(add_nk_cue, bg=bg_color)
        outputs_buttons = []

        selected_output = IntVar(outputs_frame)

        def show_current_route():
            current_route = ScpaViaIP2SL(ip=device['ip_address']).get_status(output=selected_output.get())
            if current_route != 0:
                inputs_buttons[current_route-1].flash()
                inputs_buttons[current_route-1].select()

        for output in range(1, int(total_outputs) + 1):
            if has_labels:
                output_label = f"{str(output)}: {output_labels[output-1]}"
            else:
                output_label = f"Output {str(output)}"

            outputs_buttons.append(Radiobutton(outputs_frame,
                                               bg=bg_color,
                                               fg=text_color,
                                               selectcolor=bg_color,
                                               font=(font, other_text_size-2),
                                               text=output_label,
                                               variable=selected_output,
                                               value=output,
                                               command=show_current_route))

        for iteration, button in enumerate(outputs_buttons):
            row = math.floor(iteration/6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        def add():
            self.current_cues.append({
                'uuid': device['uuid'],
                'input': selected_input.get(),
                'output': selected_output.get()
            })

            self.__update_cues_display()
            add_nk_cue.destroy()

        okay = Button(add_nk_cue, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Cue', command=add)

        outputs_frame.pack(anchor='w', pady=20)
        inputs_frame.pack(anchor='w', pady=20)
        okay.pack()

    def __add_pvp_cue(self, device):
            add_pvp_cue_window = Tk()
            add_pvp_cue_window.config(bg=bg_color)

            pvp_data = pvp(ip=device['ip_address'], port=device['port']).get_pvp_data()

            playlist_names = []
            for playlist in pvp_data['playlist']['children']:
                playlist_names.append(playlist['name'])

            playlist_buttons = []
            for iteration, playlist in enumerate(playlist_names):
                playlist_buttons.append(Button(add_pvp_cue_window,
                                               text=playlist,
                                               font=(font, plan_text_size),
                                               bg=bg_color,
                                               fg=text_color,
                                               command=lambda iteration=iteration:
                                               (playlist_button_clicked(playlist_index=iteration),
                                                add_pvp_cue_window.destroy())))
            for button in playlist_buttons:
                button.pack()

            def playlist_button_clicked(playlist_index):
                add_cg3_cue_buttons_window = Tk()
                add_cg3_cue_buttons_window.config(bg=bg_color)

                playlist_uuid = pvp_data['playlist']['children'][playlist_index]['uuid']

                cue_names = []
                for cue_name in pvp_data['playlist']['children'][playlist_index]['items']:
                    cue_names.append(cue_name['name'])

                cue_uuids = []
                for cue_name in pvp_data['playlist']['children'][playlist_index]['items']:
                    cue_uuids.append(cue_name['uuid'])

                cue_buttons = []
                for  name, uuid in zip(cue_names, cue_uuids):
                    cue_buttons.append(Button(add_cg3_cue_buttons_window,
                                              text=name,
                                              font=(font, plan_text_size),
                                              bg=bg_color,
                                              fg=text_color,
                                              command=lambda name=name, uuid=uuid:
                                              (cue_button_clicked(cue_name=name, cue_uuid=uuid, playlist_uuid=playlist_uuid),
                                               add_cg3_cue_buttons_window.destroy())))

                for button in cue_buttons:
                    button.pack()

            def cue_button_clicked(cue_name, cue_uuid, playlist_uuid):
                self.current_cues.append({
                    'uuid': device['uuid'],
                    'playlist_uuid': playlist_uuid,
                    'cue_uuid': cue_uuid,
                    'cue_name': cue_name
                })
                self.__update_cues_display()

    def __add_resi_cue(self, device):
        add_resi_cue_window = Tk()
        add_resi_cue_window.config(bg=bg_color)

        def button_pressed(command):
            add_resi_cue_window.destroy()
            self.current_cues.append({
                'uuid': device['uuid'],
                'name': commands[command]['name'],
                'command': commands[command]['command']
            })
            self.__update_cues_display()

        commands={
            1: {
                'name': 'Play',
                'command': 'CC play'
            },
            2: {
                'name': 'Pause',
                'command': 'CC pause'
            },
            3: {
                'name': 'Play and fade from black',
                'command': 'CC PAFFB'
            },
            4: {
                'name': 'Fade to black and pause',
                'command': 'CC FTBAP'
            },
            5: {
                'name': 'Fade from black (no change in playing state)',
                'command': 'CC FFB'
            },
            6: {
                'name': 'Fade to black (no change in playing state)',
                'command': 'CC FTB'
            }
        }

        resi_buttons = []
        for iteration in commands:
            resi_buttons.append(Button(add_resi_cue_window,
                                       text=commands[iteration]['name'],
                                       bg=bg_color,
                                       fg=text_color,
                                       font=(font, plan_text_size),
                                       command=lambda iteration = iteration: button_pressed(command=iteration)))
        for button in resi_buttons:
            button.pack()

    def __add_carbonite_cue(self, device, cc_labels):
        add_rosstalk_cue_window = Tk()
        add_rosstalk_cue_window.config(bg=bg_color)

        add_rosstalk_command = Label(add_rosstalk_cue_window, bg=bg_color, fg=text_color,
                                     font=(font, current_cues_text_size),
                                     anchor='w', justify='left', text='Add Rosstalk Command:')
        add_rosstalk_command.grid(row=0, column=0)

        def add_custom_control():

            custom_control_select_frame = Frame(add_rosstalk_cue_window, bg=bg_color)
            custom_control_select_frame.grid(row=1, column=0)

            for button in buttons:
                button.destroy()

            def update_cc_names(bank_int):
                # This will update the CC radiobutton names with the names from the spreadsheet when a bank is selected
                # pass an int to this function
                if cc_labels is not None:
                    logger.debug('Carbonite labels are set, recreating CC radiobuttons')
                    bank = 'bank' + str(bank_int)
                    pos = 1
                    for cc, label in zip(CCs, cc_labels[bank]):
                        if label is not None:
                            new_title =  'CC '+ str(pos) + ': ' + label
                            cc.configure(text=new_title)
                            pos += 1
                        else:
                            cc.configure(text='CC ' + str(pos))
                            pos += 1
                else:
                    logger.debug('Carbonite labels are None, passing')
                    pass

            # Create banks for bank ints to live in, add 8 bank option radiobuttons to list
            # create intvar for banks. When a radiobutton is clicked, intvar banks_var is updated. Same for CCs below
            banks = []
            banks_var = IntVar(custom_control_select_frame)
            for bank in range(8):
                banks.append(Radiobutton(custom_control_select_frame, text=f'Bank {bank + 1}',
                                         bg=bg_color,
                                         fg=text_color,
                                         font=(font, current_cues_text_size),
                                         selectcolor=bg_color,
                                         padx=20,
                                         variable=banks_var,
                                         command=lambda bank = bank: update_cc_names(bank_int = bank+1),
                                         value=(bank + 1)))

            CCs = []
            CCs_var = IntVar(custom_control_select_frame)
            for CC in range(32):
                CCs.append(Radiobutton(custom_control_select_frame, text=f'CC {CC + 1}',
                                       bg=bg_color,
                                       fg=text_color,
                                       font=(font, current_cues_text_size),
                                       selectcolor=bg_color,
                                       padx=20,
                                       variable=CCs_var,
                                       value=(CC + 1)))

            # assign bank and CC radiobuttons to grid in custom_control_select_frame frame
            for iteration, bank in enumerate(banks):
                bank.grid(row=iteration, column=0)

            for iteration, CC in enumerate(CCs):
                column_val = 1
                row_val = iteration

                if iteration > 15:
                    column_val = 2
                    row_val = iteration - 16

                CC.grid(row=row_val, column=column_val)

            # Gets banks intvar and CCs intvar values, assigns them to cues dict
            def okay_pressed(bank, CC):
                add_rosstalk_cue_window.destroy()

                if bank == 0:
                    bank = 1
                if CC == 0:
                    CC = 1

                self.current_cues.append({
                    'uuid': device['uuid'],
                    'type': 'CC',
                    'bank': bank,
                    'CC': CC
                })
                self.__update_cues_display()

            okay = Button(custom_control_select_frame,
                          bg=bg_color,
                          fg=text_color,
                          text='Add',
                          font=(font, plan_text_size),
                          command=lambda: okay_pressed(bank=banks_var.get(), CC=CCs_var.get()))
            okay.grid(row=33, column=0)

        buttons = []

        CC_btn = (Button(add_rosstalk_cue_window, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                         anchor='w', justify='left', text='Custom Control',
                         command=add_custom_control))

        buttons.append(CC_btn)

        for iteration, button in enumerate(buttons):
            button.grid(row=iteration + 2, column=0)

    def __add_kipro_cue(self):
        # creates new window for starting/stopping kipros. Either all or single.
        add_kipro_cue_window = Tk()
        add_kipro_cue_window.config(bg=bg_color)

        kipros = []

        for device in self.devices:
            if device['type'] == 'kipro':
                kipros.append({
                    'name': device['user_name'],
                    'uuid': device['uuid']
                })

        def okay_pressed():
            # when okay button in add_kipro_cue_window is pressed. start is true when command is to start recording,
            # start is false when command is to stop. 0 is to start ALL, any other int is to start any other
            # individual ones after that.

            start = start_stop_selected.get()
            kipro = kipro_selected.get()
            logger.debug('okay_button pressed in add_kipro_cue_window. start = %s, kipro = %s', start, kipro)
            self.current_cues.append({
                'start': start,
                'uuid': kipros[kipro]['uuid'],
                'name': kipros[kipro]['name']
            })
            add_kipro_cue_window.destroy()
            self.__update_cues_display()

        start_stop_frame = Frame(add_kipro_cue_window)
        start_stop_frame.config(bg=bg_color)
        start_stop_frame.grid(row=0, column=0)

        start_stop_selected = BooleanVar(start_stop_frame, value=0)

        # add start/stop buttons. Changes value of start_stop_selected variable above.
        # TRUE means start, FALSE means stop.
        Radiobutton(start_stop_frame,
             bg=bg_color,
             fg=text_color,
             text='Start',
             font=(font, current_cues_text_size),
             selectcolor=bg_color,
             padx=20,
             variable=start_stop_selected,
             value=True,
             command=lambda: logger.debug('Start_selected button pressed')
             ).pack()

        Radiobutton(start_stop_frame,
             bg=bg_color,
             fg=text_color,
             text='Stop',
             font=(font, current_cues_text_size),
             selectcolor=bg_color,
             padx=20,
             variable=start_stop_selected,
             value=False,
             command=lambda: logger.debug('Stop_selected button pressed.')
             ).pack()

        kipro_select_frame = Frame(add_kipro_cue_window)
        kipro_select_frame.config(bg=bg_color)
        kipro_select_frame.grid(row=0, column=1)

        kipro_selected = IntVar(kipro_select_frame, value=0)

        # create group of radiobuttons from kipro_data in settings.py and add them to list
        kipro_buttons = []
        for iteration, kipro in enumerate(kipros):
            kipro_buttons.append(Radiobutton(kipro_select_frame,
                                      bg=bg_color,
                                      fg=text_color,
                                      text=kipro['name'],
                                      font=(font, current_cues_text_size),
                                      selectcolor=bg_color,
                                      padx=20,
                                      variable=kipro_selected,
                                      value=iteration,
                                      command=lambda kipro=kipro: logger.debug('kipro button pressed: %s', kipro['name'])))
        for radiobutton in kipro_buttons:
            radiobutton.pack()

            Button(add_kipro_cue_window,
                         text='okay',
                         bg=bg_color,
                         fg=text_color,
                         font=(font, plan_text_size),
                         command=okay_pressed).grid(row=1, column=0)

    def __add_ez_outlet_2(self, device):
        add_ez_outlet_cue_window = Tk()
        add_ez_outlet_cue_window.configure(bg=bg_color)

        command_selected = StringVar(add_ez_outlet_cue_window, value=None)

        def okay_pressed():
            self.current_cues.append({
                'uuid': device['uuid'],
                'action': command_selected.get()
            })
            logger.debug('CueCreator.__add_ez_outlet_2 pressed. uuid %s, action %s', device['uuid'], command_selected)
            self.__update_cues_display()
            add_ez_outlet_cue_window.destroy()

        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Turn Outlet Off', selectcolor=bg_color, variable=command_selected, value='turn_off').pack()
        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Turn Outlet On', selectcolor=bg_color, variable=command_selected, value='turn_on').pack()
        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Toggle Outlet State', selectcolor=bg_color, variable=command_selected, value='toggle_state').pack()
        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Reset Outlet', selectcolor=bg_color, variable=command_selected, value='reset').pack()
        Button(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=okay_pressed).pack()

    def __add_bem104(self, device):
        add_bem104_cue_window = Tk()
        add_bem104_cue_window.configure(bg=bg_color)

        relay_selected = StringVar(add_bem104_cue_window, value=None)
        command_selected = StringVar(add_bem104_cue_window, value=None)

        left_frame = Frame(add_bem104_cue_window, bg=bg_color)
        left_frame.grid(row=0, column=0)

        right_frame = Frame(add_bem104_cue_window, bg=bg_color)
        right_frame.grid(row=0, column=1)

        Radiobutton(left_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Relay 1', selectcolor=bg_color, variable=relay_selected, value='1').pack()
        Radiobutton(left_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Relay 2', selectcolor=bg_color, variable=relay_selected, value='2').pack()

        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Switch OFF', selectcolor=bg_color, variable=command_selected, value='switch_off').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Switch ON', selectcolor=bg_color, variable=command_selected, value='switch_on').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Toggle State', selectcolor=bg_color, variable=command_selected, value='toggle').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Pulse off/on/off', selectcolor=bg_color, variable=command_selected, value='pulse_on').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Pulse on/off/on', selectcolor=bg_color, variable=command_selected, value='pulse_off').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Pulse Toggle', selectcolor=bg_color, variable=command_selected, value='pulse_toggle').pack()

        def okay_pressed():
            logger.debug('CueCreator.__add_bem104 pressed. uuid %s, relay: %s, action: %s', device['uuid'], relay_selected.get(), command_selected.get())

            if relay_selected.get() in (None, '') or command_selected.get() in (None, ''):
                messagebox.showerror(title='Please select relay and command', message='Please select a relay number and command')

            self.current_cues.append({
                'uuid': device['uuid'],
                'relay': relay_selected.get(),
                'command': command_selected.get()
            })
            self.__update_cues_display()
            add_bem104_cue_window.destroy()

        Button(add_bem104_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=okay_pressed).grid(row=1, column=0)

    def __add_controlflex(self, device):
        add_controlflex = Tk()
        add_controlflex.configure(bg=bg_color)

        all_controlflex_zones = device['zones']


        contains_qsys =  False
        for zone in device['zones']:  # if a qsys device exists, contains_qsys is true. used later for separating qsys zones
            if zone['zone_type'] == 'qsys':
                contains_qsys = True
                break

        if contains_qsys:
            qsys_zones = [] # ALL qsys zones in controlflex.
            for zone in device['zones']:
                if zone['zone_type'] == 'qsys':
                    qsys_zones.append(zone)
            qsys_zone_types = [] # list of qsys zone categories
            for qsys_zone in qsys_zones:
                if not qsys_zone['qsys_zone_type'] in qsys_zone_types:
                    qsys_zone_types.append(qsys_zone['qsys_zone_type'])


        zone_types = [] # types of controlflex zones: qsys, sony pro bravia, lighting, etc
        for zone in device['zones']:
            if not zone['zone_type'] in zone_types:
                zone_types.append(zone['zone_type'])

        controlflex_zone_frames = []

        def zone_type_selected(zone): # run when a controlflex zone is selected
            logger.debug('__add_controlflex: zone type selected: %s', zone)
            for frame in controlflex_zone_frames: # destroy frames holding controlflex zones
                frame.destroy()

            zone_command_frame = Frame(add_controlflex, bg=bg_color)
            zone_command_frame.pack()

            def command_finished(command, zone):
                add_controlflex.destroy()

                to_add = {
                    'uuid': device['uuid'],
                    'command': command,
                    'zone': zone
                }
                self.current_cues.append(to_add)
                self.__update_cues_display()

                logger.debug('__add_controlflex: command completed: %s', to_add)

            if zone['zone_type'] == 'qsys': # selected zone type is qsys
                if zone['qsys_zone_type'] == 'qsys_mute':
                    Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'MUTE {zone["friendly_name"]}', command=lambda: command_finished(command={'args': 'mute', 'value': '1'}, zone=zone)).pack()
                    Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'UNMUTE {zone["friendly_name"]}', command=lambda: command_finished(command={'args': 'mute', 'value': '0'}, zone=zone)).pack()

                if zone['qsys_zone_type'] == 'qsys_gain':
                    Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'Set {zone["friendly_name"]} to ').pack(side=LEFT)
                    percent_entry = Entry(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), width=2)
                    percent_entry.pack(side=LEFT)
                    Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='%.').pack(side=LEFT)

                    def ok():
                        command_finished(command={'args': 'gain', 'value': percent_entry.get()}, zone=zone)

                    Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=ok).pack(side=BOTTOM)

                if zone['qsys_zone_type'] == 'qsys_source':
                    def ok(source_index):
                        command_finished(command={'args':'source', 'value': source_index}, zone=zone)

                    for iteration, input in enumerate(zone['friendly_input_names'], start=1):
                        Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'{input}', command=lambda iteration=iteration: ok(source_index=iteration)).pack()

            if zone['zone_type'] == 'sony_pro_bravia':
                # power
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'Set {zone["friendly_name"]} power ').grid(row=0, column=0)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='ON', command=lambda: command_finished(command={'args': 'power', 'value': '1'}, zone=zone)).grid(row=0, column=1)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='OFF', command=lambda: command_finished(command={'args': 'power', 'value': '0'}, zone=zone)).grid(row=0, column=2)

                # volume
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'Set {zone["friendly_name"]} volume to ').grid(row=1, column=0)
                percent_entry = Entry(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), width=2)
                percent_entry.grid(row=1, column=1)
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='%').grid(row=1, column=2)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=lambda: command_finished(command={'args': 'volume', 'value': percent_entry.get()}, zone=zone)).grid(row=1, column=3)

                # input
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'Set {zone["friendly_name"]} input to :').grid(row=2, column=0)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Input 1', command=lambda: command_finished(command={'args': 'input','value': '1'}, zone=zone)).grid(row=2, column=1)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Input 2', command=lambda: command_finished(command={'args': 'input','value': '2'}, zone=zone)).grid(row=2, column=2)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Input 3', command=lambda: command_finished(command={'args': 'input','value': '2'}, zone=zone)).grid(row=2, column=3)


        for zone_type in zone_types: # add a frame for each controlflex zone type. Sony bravia, qsys, etc
            zone_frame = Frame(add_controlflex, bg=bg_color)
            zone_frame.pack(side=LEFT, anchor='n', padx=40)
            controlflex_zone_frames.append(zone_frame)

            if zone_type == 'qsys':
                qsys_zone_frames = []
                for qsys_zone_type in qsys_zone_types: # if type is qsys, create a frame for each qsys zone type. name will match index of zone type above in qsys_zone_types
                    frame = Frame(zone_frame, bg=bg_color)
                    qsys_zone_frames.append(frame)
                    frame.pack(pady=15, side=BOTTOM)
                    Label(frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=qsys_zone_type).pack()

            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'{zone_type}:').pack(padx=10, pady=2, side=TOP) # create label for type of controlflex zone.

            for controlflex_zone in all_controlflex_zones:
                if controlflex_zone['zone_type'] == zone_type:  # separate controlflex zone devices into groups
                    if zone_type == 'qsys':
                        qsys_zone_frame = qsys_zone_frames[qsys_zone_types.index(controlflex_zone['qsys_zone_type'])]
                        Button(qsys_zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=controlflex_zone['friendly_name'], command=lambda controlflex_zone=controlflex_zone: zone_type_selected(controlflex_zone)).pack(padx=10, pady=2)
                    else:
                        Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=controlflex_zone['friendly_name'], command=lambda controlflex_zone = controlflex_zone: zone_type_selected(controlflex_zone)).pack(padx=10, pady=2)

            if zone_type == 'sony_pro_bravia':
                Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='All Sony Pro Bravias', command=lambda zone_type = zone_type: zone_type_selected({'zone_type': 'all_sony_pro_bravias'})).pack(padx=10, pady=10)

    def __add_aja_kumo(self, device):
        add_kumo = Tk()
        add_kumo.configure(bg=bg_color)

        kumo_api = AJAKumo(ip=device['ip_address'])

        total_inputs = kumo_api.num_source
        total_outputs = kumo_api.num_dest

        input_names = kumo_api.get_all_source_names()
        output_names = kumo_api.get_all_dest_names()

        inputs_frame = Frame(add_kumo, bg=bg_color)
        inputs_buttons = []

        selected_input = IntVar(inputs_frame)

        for iteration, input in enumerate(input_names, start=1):
            if input is None:
                input = f'Input {iteration}'

            inputs_buttons.append(Radiobutton(inputs_frame,
                                              bg=bg_color,
                                              selectcolor=bg_color,
                                              fg=text_color, font=(font, other_text_size-2),
                                              text=input,
                                              variable=selected_input,
                                              value=iteration))

        for iteration, button in enumerate(inputs_buttons):
            row = math.floor(iteration/6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        outputs_frame = Frame(add_kumo, bg=bg_color)

        selected_output = IntVar(outputs_frame)
        selected_output.set(value=1)

        outputs_buttons = []

        def show_current_route():
            current_route = kumo_api.get_route_from_dest(selected_output.get())
            inputs_buttons[current_route-1].flash()
            inputs_buttons[current_route-1].select()

        for iteration, output in enumerate(output_names, start=1):
            if output is None:
                output = f'Output {iteration}'

            outputs_buttons.append(Radiobutton(outputs_frame,
                                               bg=bg_color,
                                               fg=text_color,
                                               selectcolor=bg_color,
                                               font=(font, other_text_size-2),
                                               text=output,
                                               variable=selected_output,
                                               value=iteration,
                                               command=show_current_route))

        for iteration, button in enumerate(outputs_buttons):
            row = math.floor(iteration/6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        def add():
            self.current_cues.append({
                'uuid': device['uuid'],
                'input': selected_input.get(),
                'output': selected_output.get()
            })

            self.__update_cues_display()
            add_kumo.destroy()

        okay = Button(add_kumo, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Cue', command=add)

        outputs_frame.pack(anchor='w', padx=20, pady=10)
        inputs_frame.pack(anchor='w', padx=20, pady=10)
        okay.pack()

    def __add_reminder_cue_clicked(self):
        # creates a new window for adding a reminder with minutes, seconds, reminder text, and okay.
        logger.debug('add reminder button clicked')
        add_reminder_window = Tk()
        add_reminder_window.config(bg=bg_color)

        def okay_pressed():
            minutes = minutes_entry.get()
            seconds = seconds_entry.get()
            reminder = reminder_entry.get()
            if minutes == '':
                minutes = 0
            if seconds == '':
                seconds = 0

            self.current_cues.append({
                'uuid': 'b652b57e-c426-4f83-87f3-a7c4026ec1f0',
                'device': 'reminder',
                'minutes': int(minutes),
                'seconds': int(seconds),
                'reminder': str(reminder)
            })
            self.__update_cues_display()

            logger.debug('Okay button pressed on add_reminder_window. Minutes: %s, '
                          'Seconds: %s, Str: %s', minutes, seconds, reminder)
            add_reminder_window.destroy()

        time_entry_frame = Frame(add_reminder_window)
        time_entry_frame.config(bg=bg_color)
        time_entry_frame.grid(row=1, column=0)

        Label(add_reminder_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', text='Add reminder after x time:').grid(row=0, column=0)

        Label(time_entry_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', text='Add reminder in: ').grid(row=1, column=0)

        minutes_entry = Entry(time_entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        minutes_entry.grid(row=1, column=2)

        Label(time_entry_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', text='minutes, ').grid(row=1, column=3)

        seconds_entry = Entry(time_entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        seconds_entry.grid(row=1, column=4)

        Label(time_entry_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', text='seconds.').grid(row=1, column=5)

        reminder_entry = Entry(add_reminder_window, width=100, bg=text_entry_box_bg_color, fg=text_color, font=(font, plan_text_size))
        reminder_entry.grid(row=2, column=0)

        Button(add_reminder_window, bg=bg_color, fg=text_color, font=(font, plan_text_size), anchor='w', text='okay', command=okay_pressed).grid(row=3, column=0)

    def __add_pause_cue_clicked(self):
        add_pause_window = Tk()
        add_pause_window.config(bg=bg_color)

        add_pause_for_x_seconds = Label(add_pause_window, bg=bg_color, fg=text_color,
                                        font=(font, current_cues_text_size),
                                        anchor='w', justify='left', text='Add pause for ___ seconds:')
        add_pause_for_x_seconds.grid(row=0, column=0)

        seconds = [.25, .5, .75, 1, 2, 3, 5, 10]

        for iteration, x in enumerate(seconds):
            seconds_button = Button(add_pause_window, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                                    anchor='w', justify='left', text=f'{x} Seconds',
                                    command=lambda x=x: (add_pause_button_clicked(seconds=x)))
            seconds_button.grid(row=1, column=iteration)

        def add_pause_button_clicked(seconds):
            self.current_cues.append({
                'uuid': 'f0d73b84-60b1-4c1d-a49f-f3b11ea65d3f',
                'device': 'pause',
                'time': seconds
            })
            add_pause_window.destroy()
            self.__update_cues_display()

    def __add_advance_cue(self):
        add_advance_window = Tk()
        add_advance_window.config(bg=bg_color)

        description_frame = Frame(add_advance_window, bg=bg_color)
        description_frame.pack()

        advance_description = Label(description_frame, bg=bg_color, fg=text_color,
                                    font=(font, current_cues_text_size),
                                    anchor='w', justify='left', text='Advance to the next item at a certain time, ONLY if current item is still live. Multiple times can be entered if you have more than 1 service.\nPress "Add Time" to add another entry and "Okay" when you are finished.')
        advance_description.grid(row=0, column=0)

        entry_frame = Frame(add_advance_window, bg=bg_color)
        entry_frame.pack()

        total_times = 0

        hours_entries = []
        minutes_entries = []
        seconds_entries = []

        def add_advance_time():
            nonlocal total_times
            total_times += 1

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=f'Advance to next item at       ').grid(row=total_times, column=0)

            hours_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size+1))
            hours_entry.grid(row=total_times, column=1)
            hours_entries.append(hours_entry)

            Label(entry_frame, bg=bg_color, fg=text_color,
                                    font=(font, current_cues_text_size),
                                    anchor='w', justify='left', text=':').grid(row=total_times, column=2)

            minutes_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size+1))
            minutes_entry.grid(row=total_times, column=3)
            minutes_entries.append(minutes_entry)

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=':').grid(row=total_times, column=4)

            seconds_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size+1))
            seconds_entry.grid(row=total_times, column=5)
            seconds_entries.append(seconds_entry)

        def okay_pressed():

            times = []
            for hour, minute, second in zip(hours_entries, minutes_entries, seconds_entries):
                hour = hour.get()
                hour = hour if len(hour) > 1 else '0' + hour

                minute = minute.get()
                minute = minute if len(minute) > 1 else '0' + minute

                second = second.get()
                second = second if len(second) > 1 else '0' + second

                times.append([hour, minute, second])

            has_previous_times = False
            previous_advance_cue_index = None

            for iteration, cue in enumerate(self.current_cues):
                if cue['uuid'] == advance_on_next_uuid:
                    has_previous_times = True
                    previous_advance_cue_index = iteration

            if not has_previous_times:
                self.current_cues.append({
                    'uuid': advance_on_next_uuid,
                    'device': 'advance_on_time',
                    'times': times
                })

            else:
                for time in times:
                    self.current_cues[previous_advance_cue_index]['times'].append(time)

            self.__update_cues_display()
            add_advance_window.destroy()

        Button(add_advance_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size+2), text='Add time', command=add_advance_time).pack()
        Button(add_advance_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size+2), text='Okay', command=okay_pressed).pack()

    def __update_cues_display(self):
        logger.debug('Updating Cues Display: Input %s', self.current_cues)

        self.current_cues_listbox.delete(0, 'end')

        for iteration, cue_verbose in enumerate(self.verbose_decode_cues(cuelist=self.current_cues)):
            self.current_cues_listbox.insert(iteration, cue_verbose)

        # advance to next display
        if self.cue_type == 'item':  # delete all existing labels/buttons, clear list
            for label, button in zip(self.advance_to_next_labels, self.advance_to_next_remove_buttons):
                label.destroy()
                button.destroy()

            self.advance_to_next_labels.clear()
            self.advance_to_next_remove_buttons.clear()

            advance_times = [] # search through all cues for single cue that contains all advance to next times, add times to list
            advance_cue_index = None
            for iteration, cue in enumerate(self.current_cues, start=0):
                if cue['uuid'] == advance_on_next_uuid:
                    advance_cue_index = iteration
                    logger.debug('advance to next cue index is %s', advance_cue_index)
                    logger.debug('cue_creator: found advance to next time: %s', cue['times'])
                    for time in cue['times']:
                        logger.debug('cue_creator: adding time %s to advance_times list', time)
                        advance_times.append(time)

            def remove_next_cue(index): # when remove button next to time is clicked, remove that time from main cue list>advance cue
                logger.debug('Removing advance to next time: %s', self.current_cues[advance_cue_index]['times'][index])
                self.current_cues[advance_cue_index]['times'].pop(index)
                self.__update_cues_display()

            for iteration, time in enumerate(advance_times, start=0): # looks at advance_times list above, creates label/button for each time
                time_str = f'{time[0]}:{time[1]}:{time[2]}'
                self.advance_to_next_labels.append(Label(self.advance_to_next_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-1), text=f'Advance to next item at {time_str}'))
                self.advance_to_next_remove_buttons.append(Button(self.advance_to_next_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-1), text='Remove', command=lambda iteration=iteration : remove_next_cue(iteration)))

            iteration = 0
            for label, button in zip(self.advance_to_next_labels, self.advance_to_next_remove_buttons):
                label.grid(row=iteration, column=0, padx=10)
                button.grid(row=iteration, column=1, padx=10)
                iteration += 1

            Frame(self.cue_creator_window, bg=separator_color, width=1, height=300).grid(row=0, column=3)
            self.advance_to_next_frame.grid(row=0, column=4)

    def __load_cue_presets_ui(self):
        pass

    def __remove_selected(self):
        logger.debug('Removing selected item: %s', self.current_cues[self.current_cues_listbox.curselection()[0]])
        self.current_cues.pop(self.current_cues_listbox.curselection()[0])
        self.current_cues_listbox.delete(self.current_cues_listbox.curselection()[0])

    def __add_cues(self): # add cues to PCO
        # if adding to individual plan item, add cues to app cues note section.
        # if adding to plan or global cues, the scheme looks like: list>list>string>dict<list<list
        #
        # [
        #   ['cue 1 name assigned by user', [{cue 1 action 1 data}{cue 1 action 2data}]
        #   ['cue 2 name assigned by user', [{cue 2 action 1 data}{cue 2 action 2 data}]
        # ]
        #
        # When adding plan, we append new data to the old data, then update the plan note with the old + new data

        if self.cue_type == 'item':
            logger.debug('cue_creator.__add_cues attempting to add cues to pco. service_type_id: %s, service_id: %s, item_id: %s, items: %s',
                          self.service_type_id, self.plan_id, self.input_item_id, self.current_cues)
            self.pco_plan.create_and_update_item_app_cue(item_id=self.input_item_id, app_cue=json.dumps(self.current_cues))

        if self.cue_type == 'plan':
            custom_cue_name = self.custom_name_entry.get()
            custom_cue_set = self.current_cues
            self.imported_cues.append([custom_cue_name, custom_cue_set])
            self.pco_plan.create_and_update_plan_app_cues(note_content=json.dumps(self.imported_cues))

        if self.cue_type == 'global':
            abs_path = os.path.dirname(__file__)
            abs_file = os.path.join(abs_path, 'global_cues.json')
            current_cue = [self.custom_name_entry.get(), self.current_cues]
            logger.debug('Writing new global cue content: %s', current_cue)

            if not os.path.exists(abs_file):  # If global_cues.json doesn't exist, create it and write cues to it
                logger.info('global_cues.json not found. Creating...')
                with open('global_cues.json', 'w') as f:
                    logger.debug('Creating global_cues.json and writing content: %s', current_cue)
                    f.writelines(json.dumps([current_cue]))

            else:  # write current cues to global_cues.json
                with open('global_cues.json', 'r') as f:
                    contents = f.read()

                    if len(contents) > 0:  # If file contains content already, append it
                        current_global_cues = json.loads(contents)

                        current_global_cues.append(current_cue)

                        with open('global_cues.json', 'w') as f_write:
                            logger.debug('appending cues to file: %s', current_global_cues)
                            f_write.writelines(json.dumps(current_global_cues))

                    else:  # if file doesn't contain cues already, write without appending
                        with open('global_cues.json', 'w') as f_write:
                            logger.debug('Writing cues to empty file: %s', current_cue)
                            f_write.writelines(json.dumps(current_cue))

        self.cue_creator_window.destroy()
        self.main_ui.reload()

    def __copy_from_plan_item(self):
        from_plan = SelectService(send_to=self)
        from_plan.ask_service_info()

    def __create_preset(self): # create preset with currently added cues
        create_preset_window = Tk()
        create_preset_window.geometry('800x100')
        create_preset_window.configure(bg=bg_color)

        Label(create_preset_window, text='Create a preset with currently added cues. Preset name:', font=(font, other_text_size), bg=bg_color, fg=text_color).pack()
        preset_name_entry = Entry(create_preset_window, font=(font, other_text_size), bg=bg_color, fg=text_color, width=75)
        preset_name_entry.pack()

        def add():  # add button clicked
            cues = []
            for cue in self.current_cues:
                if not cue['uuid'] == advance_on_next_uuid:
                    cues.append(cue)
            to_append = {
                    'name': preset_name_entry.get(),
                    'cues': cues,
                    'uuid': str(uuid.uuid4())
                }

            logger.debug('Adding cue preset to cue_presets.json: %s', to_append)

            if self.cue_presets is None:
                cue_presets = []
                cue_presets.append(to_append)

                logger.debug('cue_presets.json does not exist. Creating...')

                with open('cue_presets.json', 'w') as f:
                    f.write(json.dumps(cue_presets))

            else:
                with open('cue_presets.json', 'w') as f:
                    logger.debug('cue_presets.json exists, appending')

                    current_cue_presets = self.cue_presets
                    current_cue_presets.append(to_append)
                    f.write(json.dumps(current_cue_presets))

            # CueCreator(startup=self.startup, ui=self.main_ui, cue_type=self.cue_type, devices=self.devices).__open_cue_creator()
            create_preset_window.destroy()
            self.cue_creator_window.destroy()


        Button(create_preset_window, text='Add Preset', font=(font, other_text_size), bg=bg_color, fg=text_color, command=add).pack()


    def receive_plan_details(self, service_type_id, service_id):  # for copying actions from a specific plan item
        from_pco_plan = PcoPlan(service_type=service_type_id, plan_id=service_id)
        from_pco_plan_items = from_pco_plan.get_service_items()[1]

        copy_from_plan_item_window = Tk()
        copy_from_plan_item_window.configure(bg=bg_color)

        def select(item):
            copy_from_plan_item_window.destroy()
            cues = item['notes']['App Cues']
            for cue in cues:
                self.current_cues.append(cue)
            self.__update_cues_display()

        item_frames = []
        item_separators = []
        for iteration, item in enumerate(from_pco_plan_items):
            if item['type'] != 'header' and 'App Cues' in (item['notes'].keys()):
                frame = Frame(copy_from_plan_item_window, bg=bg_color)
                item_frames.append(frame)

                Label(frame, bg=bg_color, fg=text_color, font=(font, 12), text=item['title'], justify=LEFT).pack(side=LEFT, padx=10, pady=10, anchor='w')
                verbose_title = ''
                for verbose in self.verbose_decode_cues(item['notes']['App Cues']):
                    verbose_title += verbose + '\n'
                Label(frame, bg=bg_color, fg=text_color, font=(font, 7), text=verbose_title, justify=LEFT).pack(side=LEFT, padx=10, anchor='w')
                Button(frame, bg=bg_color, fg=text_color, text='Select', font=(font, 12), command=lambda item=item: select(item)).pack(side=RIGHT, padx=10, anchor='e')

                separator = Frame(copy_from_plan_item_window, bg=separator_color, width=500, height=1)
                separator.pack_propagate(0)
                item_separators.append(separator)

        for frame, separator in zip(item_frames, item_separators):
            frame.pack(anchor='e')
            separator.pack(pady=4)

    def __test(self):
        t = threading.Thread(target=lambda: self.activate_cues(cues=self.current_cues))
        t.start()
        t.join()