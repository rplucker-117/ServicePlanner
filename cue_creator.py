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
from ross_scpa import ScpaViaIP2SL
from ez_outlet_2 import EZOutlet2

class CueCreator:
    def __init__(self, startup, ui, cue_type='item', devices=None):

        self.service_type_id = startup.service_type_id
        self.plan_id = startup.service_id
        self.cue_type = cue_type

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

        self.current_cues_display = Label(self.current_cues_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), justify=LEFT)

        # elements for is type is 'plan' cue
        self.custom_name_frame = Frame(self.bottom_frame, bg=bg_color)
        self.custom_name_entry = Entry(self.custom_name_frame, width=40, bg=text_entry_box_bg_color, fg=text_color, font=(font, plan_text_size))

        self.input_item_id = None
        self.input_item = None
        self.cues_display_text = str()
        self.current_cues = []

        self.devices = devices

        self.all_kipros = []
        if self.devices is not None:
            for device in self.devices:
                if device['type'] == 'kipro' and not device['uuid'] == '07af78bf-9149-4a12-80fc-0fa61abc0a5c':
                    self.all_kipros.append(device)

        if self.cue_type == 'plan':
            self.imported_cues = self.pco_plan.get_plan_app_cues()
            if self.imported_cues is None:
                self.imported_cues = []

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

                if device['type'] == 'pvp':
                    cue_verbose = f"{device['user_name']}:   Cue {cue['cue_name']}"
                    cues_verbose_list.append(cue_verbose)

                if device['type'] == 'Pause':
                    cue_verbose = f"{cue['device']}:   {cue['time']} seconds."
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
                    cue_verbose = f"{cue['device']}:   {cue['name']}"
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


            return cues_verbose_list

    def activate_cues(self, cues):
        logger.debug('activate_cues called, cues input: %s', cues)
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

                    # todo add nk

                    else:
                        logger.warning('Received cue not in activate_cues list: %s', cue)
                        pass

    def __get_device_user_name_from_uuid(self, uuid):
        for device in self.devices:
            if device['uuid'] == uuid:
                return device

    def __open_cue_creator(self, overwrite):

        if overwrite is False:
            existing_cues = self.input_item['notes']['App Cues']
            for existing_cue in existing_cues:
                self.current_cues.append(existing_cue)

        self.cue_creator_window.deiconify()

        self.current_cues_frame.grid(row=0, column=0)
        self.cue_type_buttons_frame.grid(row=0, column=2)
        self.bottom_frame.grid(row=2, column=0)
        self.bottom_buttons_frame.grid(row=1, column=0)

        # Current cues display
        self.current_cues_frame.pack_propagate(0)
        cues_to_add_label = Label(self.current_cues_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Cues to Add:')
        cues_to_add_label.pack(anchor='nw')
        self.current_cues_display.pack(anchor='nw')

        if self.cue_type == 'item':
            try:
                cues_to_add_label.configure(text=f"Cues to add to {self.input_item['title']}:")
                logger.debug(f"cue_creator.__open_cue_creator: changed label to       {cues_to_add_label.cget('text')}")
            except Exception as e:
                logger.error(f"cue_creator.__open_cue_creator exception: {e}")

        # Separator frames
        Frame(self.bottom_frame, bg=separator_color, width=600, height=1).grid(row=0, column=0) # Above bottom buttons
        Frame(self.cue_creator_window, bg=separator_color, width=1, height=300).grid(row=0, column=1) # Left of cue type buttons

        # If plan cue, add custom name
        if self.cue_type in ('plan', 'global'):
            self.custom_name_frame.grid(row=0, column=0)
            Label(self.custom_name_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Plan Cue Name').pack()
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

        includes_kipro = None

        if self.devices is not None:
            for device in self.devices:
                if not device['type'] == 'kipro':
                    if not device['type'] in ('pause', 'reminder', 'kipro_all'):
                        button_name = 'Add ' + device['user_name'] + '(' + device['type'] + ')' + ' cue'
                        Button(self.cue_type_buttons_frame, text=button_name, font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=lambda device=device: add_cue_clicked(device)).pack()
                elif device['type'] == 'kipro' and includes_kipro is not True:
                    Button(self.cue_type_buttons_frame, text='Add KiPro Cue', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_kipro_cue).pack()
                    includes_kipro = True

        Button(self.cue_type_buttons_frame, text='Add Pause', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_pause_cue_clicked).pack()
        Button(self.cue_type_buttons_frame, text='Add Reminder', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_reminder_cue_clicked).pack()

        # Bottom Buttons
        Button(self.bottom_buttons_frame, text='Test', font=(font, plan_text_size), bg=bg_color, fg=text_color, command=self.__test).grid(row=1, column=0)
        Button(self.bottom_buttons_frame, text='Add Cue(s)', font=(font, plan_text_size), bg=bg_color, fg=text_color, command=self.__add_cues).grid(row=1, column=1)
        Button(self.bottom_buttons_frame, text='Cancel', font=(font, plan_text_size), bg=bg_color, fg=text_color, command=lambda: self.cue_creator_window.destroy()).grid(row=1, column=2)

        self.__update_cues_display()

    def __add_nk_scpa_ip2sl_cue(self, device):  #todo
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
        selected_input = None

        def assign_input(input):
            selected_input = input

        for input in range(1, int(total_inputs) + 1):
            if has_labels:
                input_label = f"{str(input)}:  {input_labels[input-1]}"
            else:
                input_label = f"Input {str(input)}"

            inputs_buttons.append(Radiobutton(inputs_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-2), text=input_label,
                                              command=lambda input=input: assign_input(input)))

        for iteration, button in enumerate(inputs_buttons):
            row = math.floor(iteration/6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        #  outputs radiobuttons

        outputs_frame = Frame(add_nk_cue, bg=bg_color)
        outputs_buttons = []
        selected_output = None

        def assign_output(output):  #todo when output clicked, get status and show to user
            ScpaViaIP2SL(ip=device['ip_address']).get_status(output=output)
            selected_output = output

        for output in range(1, int(total_outputs) + 1):
            if has_labels:
                output_label = f"{str(output)}: {output_labels[output-1]}"
            else:
                output_label = f"Outpur {str(output)}"

            outputs_buttons.append(Radiobutton(outputs_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-2), text=output_label,
                                              command=lambda output=output: assign_output(output)))

        for iteration, button in enumerate(outputs_buttons):
            row = math.floor(iteration/6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        outputs_frame.pack(anchor='w', pady=20)
        inputs_frame.pack(anchor='w', pady=20)

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
                CC.grid(row=iteration, column=1)

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
                'device': 'pause',
                'time': seconds
            })
            add_pause_window.destroy()
            self.__update_cues_display()

    def __update_cues_display(self):
        logger.debug('Updating Cues Display: Input %s', self.current_cues)
        self.cues_display_text = str()
        for cue_verbose in self.verbose_decode_cues(cuelist=self.current_cues):
            self.cues_display_text = self.cues_display_text + cue_verbose + '\n'
        self.current_cues_display.configure(text=self.cues_display_text)

    def __add_cues(self):
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

    def __test(self):
        t = threading.Thread(target=lambda: self.activate_cues(cues=self.current_cues))
        t.start()
        t.join()