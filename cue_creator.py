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
from cue_coder import cue_coder
from rosstalk import rosstalk as rt
from kipro import *


class CueCreator:
    def __init__(self, service_type_id, plan_id, ui, cue_type='item'):
        self.service_type_id = service_type_id
        self.plan_id = plan_id
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

        # elements for is type is 'global' cue
        self.custom_name_frame = Frame(self.bottom_frame, bg=bg_color)
        self.custom_name_entry = Entry(self.custom_name_frame, width=40, bg=text_entry_box_bg_color, fg=text_color, font=(font, plan_text_size))

        self.input_item_id = None
        self.input_item = None
        self.cues_display_text = str()
        self.current_cues = []

        # runs if input cue is global
        if self.cue_type == 'global':
            self.imported_cues = self.pco_plan.get_plan_app_cues()
            if self.imported_cues is None:
                self.imported_cues = []

    def create_cues(self, input_item):
        try:
            if 'App Cues' in input_item['notes']:
                yes_no = messagebox.askyesno('Overwrite existing cues', message="There's existing cues on this item. Do you want to overwrite them?")
                if yes_no: # User chose to delete existing cues
                    logger.debug('create_cues: Overwriting existing cues')
                    self.__open_cue_creator(overwrite=True)
                if not yes_no: # User chose to append onto existing cues
                    self.input_item = input_item
                    self.__open_cue_creator(overwrite=False)
            else: # No cues exist
                self.__open_cue_creator(overwrite=None)
        except TypeError:
            self.input_item = input_item
            self.__open_cue_creator(overwrite=None)

        # input_item_id is None if setting a global cue
        try:
            self.input_item_id = input_item['id']
        except TypeError:
            logger.debug('CueCreator.create_cues: Creating global cue, no input item')

    def verbose_decode_cues(self, cuelist):
        cues_verbose_list = []
        if cuelist is not None:
            for cue in cuelist:
                logger.debug('creating verbose output from %s', cue)
                # cg3/cg4
                if cue['device'] in ('CG3', 'CG4'):
                    cue_verbose = f"{cue['device']}:   Cue {cue['cue_name']}"
                    cues_verbose_list.append(cue_verbose)
                # pause/hold
                if cue['device'] == 'Pause':
                    cue_verbose = f"{cue['device']}:   {cue['time']} seconds."
                    cues_verbose_list.append(cue_verbose)
                # kipro
                if cue['device'] == 'Kipro':
                    if cue['start'] is True:
                        mode = 'Start'
                    if cue['start'] is False:
                        mode = 'Stop'
                    device_index = cue['kipro']
                    device_name = kipros[device_index]['name']
                    cue_verbose = f"{cue['device']}:   " \
                                  f"{mode} {device_name}"
                    cues_verbose_list.append(cue_verbose)
                # resi
                if cue['device'] == 'Resi':
                    cue_verbose = f"{cue['device']}:   {cue['name']}"
                    cues_verbose_list.append(cue_verbose)
                # reminder
                if cue['device'] == 'Reminder':
                    reminder_to_display = cue['reminder'][0:40]
                    cue_verbose = f"{cue['device']}:   {cue['minutes']}m, {cue['seconds']}s: " \
                                  f"{reminder_to_display}"
                    cues_verbose_list.append(cue_verbose)
                # rosstalk
                if cue['device'] == 'Rosstalk':
                    if cue['type'] == 'CC':
                        cue_verbose = f"{cue['device']}:" \
                                      f"   {cue['type']}:{cue['bank']}:{cue['CC']}"
                        cues_verbose_list.append(cue_verbose)
                    if cue['type'] == 'KEYCUT':
                        cue_verbose = f"{cue['device']}:   KeyAuto:" \
                                      f" {cue['bus']}: Key {cue['key']}"
                        cues_verbose_list.append(cue_verbose)
                    if cue['type'] == 'KEYAUTO':
                        cue_verbose = f"{cue['device']}:   KeyAuto:" \
                                      f" {cue['bus']}: Key {cue['key']}"
                        cues_verbose_list.append(cue_verbose)
            return cues_verbose_list

    def activate_cues(self, cues):
        logger.debug('activate_cues called, cues input: %s', cues)
        for cue in cues:
            # pvp
            if cue['device'] in ('CG3', 'CG4'):
                if cue['device'] == 'CG3':
                    ip = cg3_ip
                    port = cg3_port
                if cue['device'] == 'CG4':
                    ip = cg4_ip
                    port = cg4_port
                logger.debug('activate_cues: cueing PVP %s cue, %s', cue['device'], cue['cue_name'])
                pvp.cue_clip(ip=ip, port=port, playlist=cue['playlist_index'], clip_number=cue['cue_index'])

            # rosstalk
            elif cue['device'] == 'Rosstalk':
                if cue['type'] == 'CC':
                    command = f"CC {cue['bank']}:{cue['CC']}"
                    logger.debug('activate_cues: cueing rosstalk: %s', command)
                    rt(rosstalk_ip=rosstalk_ip, rosstalk_port=rosstalk_port, command=command)

            # kipro
            elif cue['device'] == 'Kipro':
                if cue['start']:
                    if not cue['kipro'] == 0:
                        logger.debug('activate_cues: starting single kipro %s', cue['kipro'])
                        kipro.start_absolute(ip=kipros[cue['kipro']]['ip'],
                                             name=kipros[cue['kipro']]['name'],
                                             include_date=True)
                    if cue['kipro'] == 0:
                        logger.debug('activate_cues: starting all kipros')
                        for kipro_number in range(1, len(kipros)):
                            kipro.start_absolute(ip=kipros[kipro_number]['ip'],
                                                 name=kipros[kipro_number]['name'],
                                                 include_date=True)
                if not cue['start']:
                    if not cue['kipro'] == 0:
                        logger.debug('activate_cues: stopping single kipro: %s', cue['kipro'])
                        kipro.transport_stop(ip=kipros[cue['kipro']]['ip'])
                    if cue['kipro'] == 0:
                        logger.debug('activate_cues: stopping all kipros')
                        for kipro_number in range(1, len(kipros)):
                            kipro.transport_stop(ip=kipros[kipro_number]['ip'])
            # Resi
            elif cue['device'] == 'Resi':
                logger.debug('activate_cues: resi: %s', cue['command'])
                rt(rosstalk_ip=resi_ip, rosstalk_port=resi_port, command=cue['command'])
            else:
                logger.debug('Received cue not in activate_cues list: %s', cue)
                pass

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
        Label(self.current_cues_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Cues to Add:').pack(anchor='nw')
        self.current_cues_display.pack(anchor='nw')

        # Separator frames
        Frame(self.bottom_frame, bg=separator_color, width=600, height=1).grid(row=0, column=0) # Above bottom buttons
        Frame(self.cue_creator_window, bg=separator_color, width=1, height=300).grid(row=0, column=1) # Left of cue type buttons

        # If global cue, add custom name
        if self.cue_type == 'global':
            self.custom_name_frame.grid(row=0, column=0)
            Label(self.custom_name_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Global Cue Name').pack()
            self.custom_name_entry.pack()

        # Cue type buttons
        Button(self.cue_type_buttons_frame, text='Add CG3 PVP cue', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_cg3_cue_clicked).pack()
        Button(self.cue_type_buttons_frame, text='Add CG4 PVP cue', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_cg4_cue_clicked).pack()
        Button(self.cue_type_buttons_frame, text='Add Rosstalk cue', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_rosstalk_cue_clicked).pack()
        Button(self.cue_type_buttons_frame, text='Add KiPro cue', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_kipro_cue_clicked).pack()
        Button(self.cue_type_buttons_frame, text='Add Resi cue', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_resi_cue_clicked).pack()
        Button(self.cue_type_buttons_frame, text='Add Pause', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_pause_cue_clicked).pack()
        Button(self.cue_type_buttons_frame, text='Add Reminder', font=(font, options_button_text_size), bg=bg_color, fg=text_color, command=self.__add_reminder_cue_clicked).pack()

        # Bottom Buttons
        Button(self.bottom_buttons_frame, text='Test', font=(font, plan_text_size), bg=bg_color, fg=text_color, command=self.__test).grid(row=1, column=0)
        Button(self.bottom_buttons_frame, text='Add to Planning Center', font=(font, plan_text_size), bg=bg_color, fg=text_color, command=self.__add_to_pco).grid(row=1, column=1)
        Button(self.bottom_buttons_frame, text='Cancel', font=(font, plan_text_size), bg=bg_color, fg=text_color, command=lambda: self.cue_creator_window.destroy()).grid(row=1, column=2)

        self.__update_cues_display()

    def __add_cg3_cue_clicked(self):
            add_cg3_cue_window = Tk()
            add_cg3_cue_window.config(bg=bg_color)
            data = pvp.get_pvp_data(ip=cg3_ip, port=cg3_port)

            playlist_names = []
            for playlist in data['playlist']['children']:
                playlist_names.append(playlist['name'])

            playlist_buttons = []
            for iteration, playlist in enumerate(playlist_names):
                playlist_buttons.append(Button(add_cg3_cue_window,
                                               text=playlist,
                                               font=(font, plan_text_size),
                                               bg=bg_color,
                                               fg=text_color,
                                               command=lambda iteration=iteration:
                                               (playlist_button_clicked(playlist_index=iteration),
                                                add_cg3_cue_window.destroy())))
            for button in playlist_buttons:
                button.pack()

            def playlist_button_clicked(playlist_index):
                add_cg3_cue_buttons_window = Tk()
                add_cg3_cue_buttons_window.config(bg=bg_color)

                cue_names = []
                for cue_name in data['playlist']['children'][playlist_index]['items']:
                    cue_names.append(cue_name['name'])

                cue_buttons = []
                for iteration, cue_name in enumerate(cue_names):
                    cue_buttons.append(Button(add_cg3_cue_buttons_window,
                                              text=cue_name,
                                              font=(font, plan_text_size),
                                              bg=bg_color,
                                              fg=text_color,
                                              command=lambda iteration=iteration, cue_name=cue_name:
                                              (cue_button_clicked(playlist_index=playlist_index, cue_index=iteration,
                                                                  cue_name=cue_name),
                                               add_cg3_cue_buttons_window.destroy())))

                for button in cue_buttons:
                    button.pack()

            def cue_button_clicked(playlist_index, cue_index, cue_name):
                self.current_cues.append({
                    'device': 'CG3',
                    'playlist_index': playlist_index,
                    'cue_index': cue_index,
                    'cue_name': cue_name}
                )
                self.__update_cues_display()

    def __add_cg4_cue_clicked(self):
            add_cg4_cue_window = Tk()
            add_cg4_cue_window.config(bg=bg_color)
            data = pvp.get_pvp_data(ip=cg4_ip, port=cg4_port)

            playlist_names = []
            for playlist in data['playlist']['children']:
                playlist_names.append(playlist['name'])

            playlist_buttons = []
            for iteration, playlist in enumerate(playlist_names):
                playlist_buttons.append(Button(add_cg4_cue_window,
                                               text=playlist,
                                               font=(font, plan_text_size),
                                               bg=bg_color,
                                               fg=text_color,
                                               command=lambda iteration=iteration:
                                               (playlist_button_clicked(playlist_index=iteration),
                                                add_cg4_cue_window.destroy())))
            for button in playlist_buttons:
                button.pack()

            def playlist_button_clicked(playlist_index):
                add_cg4_cue_buttons_window = Tk()
                add_cg4_cue_buttons_window.config(bg=bg_color)

                cue_names = []
                for cue_name in data['playlist']['children'][playlist_index]['items']:
                    cue_names.append(cue_name['name'])

                cue_buttons = []
                for iteration, cue_name in enumerate(cue_names):
                    cue_buttons.append(Button(add_cg4_cue_buttons_window,
                                              text=cue_name,
                                              font=(font, plan_text_size),
                                              bg=bg_color,
                                              fg=text_color,
                                              command=lambda iteration=iteration, cue_name=cue_name:
                                              (cue_button_clicked(playlist_index=playlist_index, cue_index=iteration,
                                                                  cue_name=cue_name),
                                               add_cg4_cue_buttons_window.destroy())))

                for button in cue_buttons:
                    button.pack()

            def cue_button_clicked(playlist_index, cue_index, cue_name):
                self.current_cues.append({
                    'device': 'CG4',
                    'playlist_index': playlist_index,
                    'cue_index': cue_index,
                    'cue_name': cue_name}
                )
                self.__update_cues_display()

    def __add_rosstalk_cue_clicked(self):
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
                    'device': 'Rosstalk',
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

        def add_key_cut():
            for button in buttons:
                button.destroy()

            busses_and_keys = {
                'ME1': 4,
                'ME2': 4,
                'MME1': 2,
                'MME2': 2,
                'MME3': 2,
                'MME4': 2,
                'MS1': 2,
                'MS2': 2
            }

            # activates or deactivates key 3/4 depending on which bus source is selected
            def activate_keys_radiobuttons(bus):
                if bus in ('ME1', 'ME2'):
                    keys[2].configure(state=NORMAL)
                    keys[3].configure(state=NORMAL)
                if bus in ('MME1', 'MME2', 'MME3', 'MME4', 'MS1', 'MS2'):
                    keys[2].configure(state=DISABLED)
                    keys[3].configure(state=DISABLED)

            bus_and_key_select_frame = Frame(add_rosstalk_cue_window, bg=bg_color)
            bus_and_key_select_frame.grid(row=1, column=0)

            bus_lbl = Label(bus_and_key_select_frame, font=('Arial Bold', plan_text_size), bg=bg_color, fg=text_color,
                            text='BUS')
            bus_lbl.grid(row=0, column=0)

            bus_lbl = Label(bus_and_key_select_frame, font=('Arial Bold', plan_text_size), bg=bg_color, fg=text_color,
                            text='KEY')
            bus_lbl.grid(row=0, column=1)

            bus_selected = StringVar(bus_and_key_select_frame)

            busses = []
            for bus, keys in busses_and_keys.items():
                busses.append(Radiobutton(bus_and_key_select_frame, text=bus,
                                          variable=bus_selected,
                                          value=bus,
                                          bg=bg_color,
                                          fg=text_color,
                                          selectcolor=bg_color,
                                          font=(font, current_cues_text_size),
                                          padx=20,
                                          command=lambda bus=bus: (activate_keys_radiobuttons(bus))))

            key_selected = IntVar(bus_and_key_select_frame)
            keys = []
            for key in range(1, 5):
                keys.append(Radiobutton(bus_and_key_select_frame,
                                        text=key,
                                        variable=key_selected,
                                        value=key,
                                        bg=bg_color,
                                        fg=text_color,
                                        selectcolor=bg_color,
                                        font=(font, current_cues_text_size),
                                        padx=20))

            for iteration, bus_button in enumerate(busses):
                bus_button.grid(row=iteration + 1, column=0)

            for iteration, key_button in enumerate(keys):
                key_button.grid(row=iteration + 1, column=1)

            def okay_pressed(bus, key):
                add_rosstalk_cue_window.destroy()
                cues.update({len(cues) + 1: {
                    'device': 'Rosstalk',
                    'type': 'KEYCUT',
                    'bus': bus,
                    'key': key
                }})


            add = Button(bus_and_key_select_frame,
                         bg=bg_color,
                         fg=text_color,
                         text='Add',
                         font=(font, plan_text_size),
                         command=lambda: okay_pressed(bus=bus_selected.get(), key=key_selected.get()))
            add.grid(row=8, column=0)

        def add_key_auto():
            for button in buttons:
                button.destroy()

            busses_and_keys = {
                'ME1': 4,
                'ME2': 4,
                'MME1': 2,
                'MME2': 2,
                'MME3': 2,
                'MME4': 2,
                'MS1': 2,
                'MS2': 2
            }

            # activates or deactivates key 3/4 depending on which bus source is selected.
            # me1/me2 are the only busses with all 4 keys available
            def activate_keys_radiobuttons(bus):
                if bus in ('ME1', 'ME2'):
                    keys[2].configure(state=NORMAL)
                    keys[3].configure(state=NORMAL)
                if bus in ('MME1', 'MME2', 'MME3', 'MME4', 'MS1', 'MS2'):
                    keys[2].configure(state=DISABLED)
                    keys[3].configure(state=DISABLED)

            bus_and_key_select_frame = Frame(add_rosstalk_cue_window, bg=bg_color)
            bus_and_key_select_frame.grid(row=1, column=0)

            bus_lbl = Label(bus_and_key_select_frame, font=('Arial Bold', plan_text_size), bg=bg_color, fg=text_color,
                            text='BUS')
            bus_lbl.grid(row=0, column=0)

            bus_lbl = Label(bus_and_key_select_frame, font=('Arial Bold', plan_text_size), bg=bg_color, fg=text_color,
                            text='KEY')
            bus_lbl.grid(row=0, column=1)

            bus_selected = StringVar(bus_and_key_select_frame)

            busses = []
            for bus, keys in busses_and_keys.items():
                busses.append(Radiobutton(bus_and_key_select_frame, text=bus,
                                          variable=bus_selected,
                                          value=bus,
                                          bg=bg_color,
                                          fg=text_color,
                                          selectcolor=bg_color,
                                          font=(font, current_cues_text_size),
                                          padx=20,
                                          command=lambda bus=bus: (activate_keys_radiobuttons(bus))))

            key_selected = IntVar(bus_and_key_select_frame)
            keys = []
            for key in range(1, 5):
                keys.append(Radiobutton(bus_and_key_select_frame,
                                        text=key,
                                        variable=key_selected,
                                        value=key,
                                        bg=bg_color,
                                        fg=text_color,
                                        selectcolor=bg_color,
                                        font=(font, current_cues_text_size),
                                        padx=20))

            for iteration, bus_button in enumerate(busses):
                bus_button.grid(row=iteration + 1, column=0)

            for iteration, key_button in enumerate(keys):
                key_button.grid(row=iteration + 1, column=1)

            def okay_pressed(bus, key):
                add_rosstalk_cue_window.destroy()
                cues.update({len(cues) + 1: {
                    'device': 'Rosstalk',
                    'type': 'KEYAUTO',
                    'bus': bus,
                    'key': key
                }})


            add = Button(bus_and_key_select_frame,
                         bg=bg_color,
                         fg=text_color,
                         text='Add',
                         font=(font, plan_text_size),
                         command=lambda: okay_pressed(bus=bus_selected.get(), key=key_selected.get()))
            add.grid(row=8, column=0)

        buttons = []

        key_cut_btn = (Button(add_rosstalk_cue_window, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                              anchor='w', justify='left', text='Key Cut',
                              command=add_key_cut))

        key_auto_btn = (Button(add_rosstalk_cue_window, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                               anchor='w', justify='left', text='Key Auto',
                               command=add_key_auto))

        CC_btn = (Button(add_rosstalk_cue_window, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                         anchor='w', justify='left', text='Custom Control',
                         command=add_custom_control))

        buttons.append(CC_btn)
        # buttons.append(key_cut_btn)
        # buttons.append(key_auto_btn)

        for iteration, button in enumerate(buttons):
            button.grid(row=iteration + 2, column=0)

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
                'device': 'Reminder',
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

        add_reminder_text_label = Label(add_reminder_window, bg=bg_color, fg=text_color,
                                  font=(font, current_cues_text_size), anchor='w',
                                  text='Add reminder after x time:').grid(row=0, column=0)

        add_reminder_in_label = Label(time_entry_frame, bg=bg_color, fg=text_color,
                                  font=(font, current_cues_text_size), anchor='w',
                                  text='Add reminder in: ').grid(row=1, column=0)

        minutes_entry = Entry(time_entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                  font=(font, current_cues_text_size))
        minutes_entry.grid(row=1, column=2)

        minutes_seconds_label = Label(time_entry_frame, bg=bg_color, fg=text_color,
                                  font=(font, current_cues_text_size), anchor='w',
                                  text='minutes, ').grid(row=1, column=3)

        seconds_entry = Entry(time_entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                  font=(font, current_cues_text_size))
        seconds_entry.grid(row=1, column=4)

        seconds_label = Label(time_entry_frame, bg=bg_color, fg=text_color,
                                  font=(font, current_cues_text_size), anchor='w',
                                  text='seconds.').grid(row=1, column=5)

        reminder_entry = Entry(add_reminder_window, width=100, bg=text_entry_box_bg_color, fg=text_color,
                                  font=(font, plan_text_size))
        reminder_entry.grid(row=2, column=0)

        okay = Button(add_reminder_window, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                              anchor='w', text='okay',
                              command=okay_pressed).grid(row=3, column=0)

    def __add_kipro_cue_clicked(self):
        # creates new window for starting/stopping kipros. Either all or single.
        add_kipro_cue_window = Tk()
        add_kipro_cue_window.config(bg=bg_color)

        def okay_pressed():
            # when okay button in add_kipro_cue_window is pressed. start is true when command is to start recording,
            # start is false when command is to stop. 0 is to start ALL, any other int is to start any other
            # individual ones after that.

            start = start_stop_selected.get()
            kipro = kipro_selected.get()
            logger.debug('okay_button pressed in add_kipro_cue_window. start = %s, kipro = %s', start, kipro)
            self.current_cues.append({
                'device': 'Kipro',
                'start': start,
                'kipro': kipro
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
                'device': 'Pause',
                'time': seconds
            })
            add_pause_window.destroy()
            self.__update_cues_display()

    def __add_resi_cue_clicked(self):
        add_resi_cue_window = Tk()
        add_resi_cue_window.config(bg=bg_color)

        def button_pressed(command):
            add_resi_cue_window.destroy()
            self.current_cues.append({
                'device': 'Resi',
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

    def __update_cues_display(self):
        logger.debug('Updating Cues Display: Input %s', self.current_cues)
        self.cues_display_text = str()
        for cue_verbose in self.verbose_decode_cues(cuelist=self.current_cues):
            self.cues_display_text = self.cues_display_text + cue_verbose + '\n'
        self.current_cues_display.configure(text=self.cues_display_text)

    def __add_to_pco(self):
        # if adding to individual plan item, add cues to app cues note section.
        # if adding to global cues, the scheme looks like: list>list>string>dict<list<list
        #
        # [
        #   ['cue 1 name assigned by user', [{cue 1 action 1 data}{cue 1 action 2data}]
        #   ['cue 2 name assigned by user', [{cue 2 action 1 data}{cue 2 action 2 data}]
        # ]
        #
        # When adding global, we append new data to the old data, then update the plan note with the old + new data

        if self.cue_type == 'item':
            logger.debug('cue_creator.__add_to_pco: attempting to add cues to pco. service_type_id: %s, service_id: %s, item_id: %s, items: %s',
                          self.service_type_id, self.plan_id, self.input_item_id, self.current_cues)
            self.pco_plan.create_and_update_item_app_cue(item_id=self.input_item_id, app_cue=json.dumps(self.current_cues))
        if self.cue_type == 'global':
            custom_cue_name = self.custom_name_entry.get()
            custom_cue_set = self.current_cues
            self.imported_cues.append([custom_cue_name, custom_cue_set])
            self.pco_plan.create_and_update_plan_app_cues(note_content=json.dumps(self.imported_cues))

        self.cue_creator_window.destroy()
        self.main_ui.reload()

    def __test(self):
        self.activate_cues(cues=self.current_cues)
