import math
import pprint
import threading
from tkinter import *
from tkinter import messagebox
from logzero import logger
import os
import json
import uuid
from typing import Union, List

from configs.settings import *

from cue_handler import CueHandler
from pvp import PVP
from ross_scpa import ScpaViaIP2SL
from select_service import SelectService
from sheet_reader import ReadSheet
from aja_kumo import AJAKumo
from pco_plan import PcoPlan
from propresenter import ProPresenter
from webos_tv import WebOSTV
from general_networking import is_host_online
import tkinter.messagebox


class CueCreator:
    def __init__(self, startup, ui, devices: List[dict]):
        """
        Main UI to create cues. This should only be called from main ui. Create a new instance
        of this window for each use.

        :param startup: Startup class in main.py file.
        :param ui: Main UI.
        :param devices: deserialized devices found in configs/devices.json
        """

        self.devices = devices

        # PCO info
        self.service_type_id = startup.service_type_id
        self.plan_id = startup.service_id

        self.cue_handler = CueHandler(devices=devices)
        self.main_ui = ui
        self.pco_plan: PcoPlan = ui.pco_plan

        # this is set by create_plan_item_cue when editing an item cue
        self.input_item: dict

        self.type_of_cues_being_edited = None
        self.type_of_cues_being_edited: str  # this will either be item, plan, or global

        #for use when creating cues on an item
        self.current_cues = {
            'action_cues': [],
            'advance_to_next_on_time': [],
            'advance_to_next_automatically': False,
            'button_color': bg_color
        }

        self.imported_plan_cues = []

        self.global_cue_shotbox_init = None
        self.global_cue_bank_being_edited: int = None
        self.global_cue_index_being_edited: int = None
        self.global_cues: List[List[dict]] = None

        self.is_editing_plan_cue = False # True if editing an existing plan cue

        self.plan_cue_index_being_edited = None
        self.plan_cue_index_being_edited: int

        # main TK
        self.cue_creator_window = Tk()
        self.cue_creator_window.withdraw()
        self.cue_creator_window.title('Cue Creator')

        # lambda ignores the automatically passed event to the function
        self.cue_creator_window.bind('<Return>', lambda event: self._save())
        self.cue_creator_window.bind('<Delete>', lambda event: self._remove_selected())
        self.cue_creator_window.bind('<Prior>', lambda event: self._move_selected_cue_up())
        self.cue_creator_window.bind('<Next>', lambda event: self._move_selected_cue_down())
        self.cue_creator_window.bind('<Escape>', lambda event: self._cancel())

        # -------------main item frames---------------
        # top left
        self.current_cues_frame = Frame(self.cue_creator_window, bg=bg_color, width=800, height=300)
        # Holds buttons for adding cues on right side
        self.cue_type_buttons_frame = Frame(self.cue_creator_window, bg=bg_color)
        # very bottom, holds separator as well as main function buttons
        self.bottom_frame = Frame(self.cue_creator_window, bg=bg_color)
        # holds add/cancel/test buttons at bottom. Child of bottom_frame
        self.bottom_buttons_frame = Frame(self.bottom_frame, bg=bg_color)
        # holds advance to next buttons on right side
        self.advance_to_next_frame = Frame(self.cue_creator_window, bg=bg_color)

        # ------------------devices/presets buttons frames --------------------------
        self.devices_buttons_frame = Frame(self.cue_type_buttons_frame, bg=bg_color)
        self.cue_presets_button_frame = Frame(self.cue_type_buttons_frame, bg=bg_color)

        # ----------------move selected up/down and current cues ------------------
        # frame to hold buttons to move selected cue up/down
        self.move_up_down_frame = Frame(self.current_cues_frame, bg=bg_color)
        self.current_cues_listbox = Listbox(self.current_cues_frame, bg=bg_color, fg=text_color,
                                            font=(font, other_text_size - 1), height=15, width=100)

        # ---------------custom name entry---------------------
        self.custom_name_frame = Frame(self.bottom_frame, bg=bg_color)
        self.custom_name_entry = Entry(self.custom_name_frame, width=40, bg=text_entry_box_bg_color,
                                       fg=text_color, font=(font, plan_text_size))

        # -------------advance to next labels and buttons--------------
        self.advance_to_next_labels = []
        self.advance_to_next_remove_buttons = []

        # auto advance to next checkbutton var
        self.auto_advance_to_next = BooleanVar(self.current_cues_frame)
        self.auto_advance_to_next_checkbutton: Checkbutton

        # read cue_presets
        self.cue_presets = self._try_read_cue_presets()

        self.cue_preset_buttons: [Button] = []

        self.includes_kipro: bool = False

    def create_plan_item_cue(self, input_item: dict = None) -> None:
        """
        Create cues on a plan item. Opens cue creator window. Meant to be called directly from "options" button from
        main cue creator window.

        :param input_item: the plan item that cues are being created for, in {'title': 'Pre-Service Playlist', 'type':
        'item', 'length': 1500, 'service_position': 'pre', 'id': '824628067','sequence': 4, 'notes':
        {'Stage': 'clear', 'Video': 'Pre-Service Media'}} format.
        :return: None.
        """

        self.type_of_cues_being_edited = 'item'
        self.input_item = input_item

        # put imported item cues into current_cues dict, open cue creator
        def import_cues() -> None:
            self.current_cues['advance_to_next_automatically'] = \
                input_item['notes']['App Cues']['advance_to_next_automatically']
            self.current_cues['advance_to_next_on_time'] = \
                input_item['notes']['App Cues']['advance_to_next_on_time']
            self.current_cues['action_cues'] = input_item['notes']['App Cues']['action_cues']

        # if app cues in input item AND those cues aren't empty
        if 'App Cues' in input_item['notes'] and input_item['notes']['App Cues'] != {
            'action_cues': [],
            'advance_to_next_on_time': [],
            'advance_to_next_automatically': False}:

            import_cues()
            self._open_cue_creator()
        else:
            self._open_cue_creator()

    def create_plan_cue(self, cuelist: List[List]) -> None:
        """
        Create a new plan cue. Opens cue creator window.

        :param cuelist: imported cues from plan cue that need to be added to cue list in order to edit
        :return: None.
        """

        self.type_of_cues_being_edited = 'plan'
        for cue in cuelist:
            self.imported_plan_cues.append(cue)

        self._open_cue_creator()

    def edit_plan_cue(self, cuelist: List[List], cue_index: int) -> None:
        """
        Edit a plan cue. Opens cue creator window.

        :param cuelist: imported cues from plan cue that need to be added to cue list in order to edit
        :param cue_index: index of plan cue that is being edited
        :return: None.
        """
        self.type_of_cues_being_edited = 'plan'
        self.is_editing_plan_cue = True
        self.plan_cue_index_being_edited = cue_index

        for cue in cuelist:
            self.imported_plan_cues.append(cue)

        self.current_cues['action_cues'] = cuelist[cue_index][1]['action_cues']
        self.custom_name_entry.insert(0, cuelist[cue_index][0])
        if 'button_color' in cuelist[cue_index][1].keys():
            self.current_cues['button_color'] = cuelist[cue_index][1]['button_color']

        self._open_cue_creator()

    def edit_global_cue(self, global_cues: List[List[dict]], cue_bank: int, cue_index: int, global_cue_shotbox_init) -> None:
        """
        Edit a global cue. Opens cue creator window.

        :param global_cues: ALL global cues
        :param cue_bank: bank that contains current cue being edited
        :param cue_index: index of cue within bank that's being edited
        :param cue_shotbox_window: root ui of the shotbox window
        :return: None.
        """

        self.global_cues = global_cues
        self.global_cue_shotbox_init = global_cue_shotbox_init

        logger.debug(f'CueCreator: Editing Global Cue {cue_bank}:{cue_index}')
        self.type_of_cues_being_edited = 'global'

        self.global_cue_bank_being_edited = cue_bank
        self.global_cue_index_being_edited = cue_index

        # this might not be needed
        for cue in self.global_cues[cue_bank][cue_index]['cues']:
            self.imported_plan_cues.append(cue)

        self.current_cues['action_cues'] = self.global_cues[cue_bank][cue_index]['cues']
        self.custom_name_entry.insert(0, self.global_cues[cue_bank][cue_index]['name'])

        self._open_cue_creator()

    def receive_plan_details(self, service_type_id: int, service_id: int) -> None:
        """
        This function should only be called from the SelectService class.
        When using __copy_cues_from_plan_item, the SelectService function is passed the
        instance of this class, which will call back this function with service_type_id and service_id details.
        This will then fill in the cues from the selected item to the current cue.

        :param service_type_id: the service type id that contains the plan that you want to copy cues from.
        :param service_id:  the service id that contains the plan that you want to copy cues from.
        :return: None.
        """

        from_pco_plan = PcoPlan(service_type=service_type_id, plan_id=service_id)
        CueHandler.check_and_update_plan_for_october_2022_cues(service_type_id=service_type_id, service_id=service_id)

        from_pco_plan_items = self.main_ui.convert_service_items_app_cues_to_dict_and_validate(from_pco_plan.get_plan_items(), push_updates_to_pco=False) #do not push updates as the underlying pco object uses incorrect plan ids

        copy_from_plan_item_window = Tk()
        copy_from_plan_item_window.configure(bg=bg_color)

        # Create main frame to hold everything that scrolls
        canvas_holder_frame = Frame(copy_from_plan_item_window, bg=bg_color)
        canvas_holder_frame.pack(fill=BOTH, expand=1)

        # create canvas inside of main frame
        container_canvas = Canvas(canvas_holder_frame, bg=bg_color, height=900, width=650)
        container_canvas.pack(side=LEFT, fill=BOTH, expand=1)

        def _on_mouse_wheel(event):
            """Mouse scroll event handler"""
            container_canvas.yview_scroll(-1 * int((event.delta / 120)), 'units')

        # add scrollbar to canvas
        scrollbar = Scrollbar(canvas_holder_frame, orient=VERTICAL, command=container_canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        # configure canvas and set scrollbar binding
        container_canvas.configure(yscrollcommand=scrollbar.set)
        container_canvas.bind('<Configure>', lambda e: container_canvas.configure(scrollregion=container_canvas.bbox('all')))
        container_canvas.bind_all('<MouseWheel>', _on_mouse_wheel)

        # Create another frame inside of canvas. All scroll-able content goes in this frame
        primary_content_frame = Frame(container_canvas, bg=bg_color)

        # add above frame to new window inside of canvas
        container_canvas.create_window((0, 0), window=primary_content_frame, anchor='nw')

        def select(item):
            copy_from_plan_item_window.destroy()

            for cue in item['notes']['App Cues']['action_cues']:
                self.current_cues['action_cues'].append(cue)

            for cue in item['notes']['App Cues']['advance_to_next_on_time']:
                self.current_cues['advance_to_next_on_time'].append(cue)

            if item['notes']['App Cues']['advance_to_next_automatically']:
                self.auto_advance_to_next_checkbutton.select()

            self._update_cues_display()

        item_frames = []
        item_separators = []
        for iteration, item in enumerate(from_pco_plan_items):
            if item['type'] != 'header' and 'App Cues' in (item['notes'].keys()):
                frame = Frame(primary_content_frame, bg=bg_color)
                item_frames.append(frame)

                Label(frame, bg=bg_color, fg=text_color, font=(font, 12), text=item['title'], justify=LEFT).pack(
                    side=LEFT, padx=10, pady=10, anchor='w')
                verbose_title = ''
                for verbose in self.cue_handler.verbose_decode_cues(item['notes']['App Cues']['action_cues']):
                    verbose_title += verbose + '\n'
                Label(frame, bg=bg_color, fg=text_color, font=(font, 7), text=verbose_title, justify=LEFT).pack(
                    side=LEFT, padx=10, anchor='w')
                Button(frame, bg=bg_color, fg=text_color, text='Select', font=(font, 12),
                       command=lambda item=item: select(item)).pack(side=RIGHT, padx=10, anchor='e')

                separator = Frame(primary_content_frame, bg=separator_color, width=500, height=1)
                separator.pack_propagate(False)
                item_separators.append(separator)

        for frame, separator in zip(item_frames, item_separators):
            frame.pack(anchor='e')
            separator.pack(pady=4)

    def _update_cues_display(self) -> None:
        """
        Updates all user-displayed cues
        :return: None.
        """

        self.current_cues_listbox.delete(0, 'end')

        for iteration, cue_verbose in enumerate(
                self.cue_handler.verbose_decode_cues(cuelist=self.current_cues['action_cues'])):
            self.current_cues_listbox.insert(iteration, cue_verbose)

        # advance to next display
        if self.type_of_cues_being_edited == 'item':  # delete all existing labels/buttons, clear list
            for label, button in zip(self.advance_to_next_labels, self.advance_to_next_remove_buttons):
                label.destroy()
                button.destroy()

            self.advance_to_next_labels.clear()
            self.advance_to_next_remove_buttons.clear()

            def remove_advance_to_next_cue(
                    index):  # when remove button next to time is clicked, remove that time from main cue list>advance cue
                logger.debug('Removing advance to next time: %s', self.current_cues['advance_to_next_on_time'][index])
                self.current_cues['advance_to_next_on_time'].pop(index)
                self._update_cues_display()

            # Create buttons and labels for advance to next stuff on the right side
            for iteration, time in enumerate(self.current_cues['advance_to_next_on_time'], start=0):
                time_str = f'{time[0]}:{time[1]}:{time[2]}'
                self.advance_to_next_labels.append(
                    Label(self.advance_to_next_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 1),
                          text=f'Advance to next item at {time_str}'))
                self.advance_to_next_remove_buttons.append(
                    Button(self.advance_to_next_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 1),
                           text='Remove', command=lambda iteration=iteration: remove_advance_to_next_cue(iteration)))

            iteration = 0
            for label, button in zip(self.advance_to_next_labels, self.advance_to_next_remove_buttons):
                label.grid(row=iteration, column=0, padx=10)
                button.grid(row=iteration, column=1, padx=10)
                iteration += 1

            Frame(self.cue_creator_window, bg=separator_color, width=1, height=300).grid(row=0, column=3)
            self.advance_to_next_frame.grid(row=0, column=4)

        self._check_cues_for_errors()

    def _open_cue_creator(self) -> None:
        """
        Configures the main ui for the cue creator window. Should not be called directly.

        :return: None
        """

        self.cue_creator_window.configure(bg=bg_color)

        self.cue_creator_window.deiconify()  # give this window focus

        # position frames where they need to go
        self.current_cues_frame.grid(row=0, column=0)
        self.cue_type_buttons_frame.grid(row=0, column=2)
        self.bottom_frame.grid(row=2, column=0)
        self.bottom_buttons_frame.grid(row=1, column=0)
        self.devices_buttons_frame.pack(side=LEFT)  # this and cue_presets_button_frame go inside cue_type_buttons_frame
        self.cue_presets_button_frame.pack(side=RIGHT, fill='y', expand=True)

        self.current_cues_frame.pack_propagate(False)
        cues_to_add_label = Label(self.current_cues_frame, bg=bg_color, fg=text_color,
                                  font=(font, other_text_size), text='Cues to Add:')

        cues_to_add_label.grid(row=0, column=1)
        self.current_cues_listbox.grid(row=1, column=1)
        self.move_up_down_frame.grid(row=1, column=0)

        if self.type_of_cues_being_edited == 'item':
            # Schedule advance to next button
            Button(self.bottom_buttons_frame, text='Schedule advance to next', font=(font, 11),
                   bg=bg_color, fg=text_color, command=lambda: self._schedule_advance_to_next()).grid(row=1, column=6)

            # "cues to add to" title
            cues_to_add_label.configure(text=f"Cues to add to {self.input_item['title']}:")

            # Advance to next on item timer finish checkbox
            self.auto_advance_to_next_checkbutton = Checkbutton(self.current_cues_frame, bg=bg_color, fg=text_color,
                                       font=(font, other_text_size), variable=self.auto_advance_to_next,
                                       selectcolor=bg_color,
                                       text='Automatically advance to next upon item timer completion')
            self.auto_advance_to_next_checkbutton.grid(row=2, column=1, sticky='w')

            if self.current_cues['advance_to_next_automatically']:
                self.auto_advance_to_next_checkbutton.select()

            # Change item length buttons
            self.update_item_length_frame = Frame(self.current_cues_frame, bg=bg_color)
            self.update_item_length_frame.grid(row=3, column=1, sticky='w')

            self.update_item_length = IntVar(self.update_item_length_frame)
            self.update_item_length_checkbutton = Checkbutton(self.update_item_length_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), variable=self.update_item_length, selectcolor=bg_color, text='Update Item Length:')
            self.update_item_length_checkbutton.grid(row=0, column=0)

            self.update_minutes = Entry(self.update_item_length_frame, bg=bg_color, font=(font, 11), fg=text_color, width=3)
            self.update_minutes.grid(row=0, column=1)

            self.update_seconds = Entry(self.update_item_length_frame, bg=bg_color, font=(font, 11), fg=text_color, width=3)
            self.update_seconds.grid(row=0, column=3)

            Label(self.update_item_length_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', justify='left', text=':').grid(row=0, column=2)

        if self.type_of_cues_being_edited == 'plan':
            button_color_frame = Frame(self.current_cues_frame, bg=bg_color)

            Label(button_color_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), text='Button Color:').grid(row=0, column=0, padx=10)

            available_colors = (bg_color, '#ff7070', '#ffaf72', '#fff172', '#98ff72', '#72ffdd', '#729dff', '#9472ff', '#ff72ca')

            def button_clicked(index):
                for button in buttons:
                    button.configure(bd=2)
                buttons[index].configure(bd=4)

                self.current_cues['button_color'] = available_colors[index]

            buttons = []

            for i, color in enumerate(available_colors):
                button = Button(button_color_frame, bg=color, width=3, height=1, command=lambda i=i: button_clicked(i))
                button.grid(row=0, column=i+1, padx=5)
                buttons.append(button)

            if self.current_cues['button_color'] in available_colors:
                index = available_colors.index(self.current_cues['button_color'])
                button_clicked(index)
            else:
                button_clicked(0)

            button_color_frame.grid(row=4, column=1, pady=20, sticky='w')

        # move selected cue up/down
        Button(self.move_up_down_frame, bg=bg_color, fg=text_color, font=(font, options_button_text_size),
               text='Move selected cue up',
               command=self._move_selected_cue_up).pack(padx=10)
        Button(self.move_up_down_frame, bg=bg_color, fg=text_color, font=(font, options_button_text_size),
               text='Move selected cue down',
               command=lambda: self._move_selected_cue_down()).pack(padx=10)

        # Separator frames
        # Above bottom buttons
        Frame(self.bottom_frame, bg=separator_color, width=600, height=1).grid(row=0, column=0)
        # Left of cue type buttons
        Frame(self.cue_creator_window, bg=separator_color, width=1, height=300).grid(row=0, column=1)

        # Custom name if cue type is not item
        if self.type_of_cues_being_edited != 'item':
            self.custom_name_frame.grid(row=0, column=0)
            Label(self.custom_name_frame, bg=bg_color, fg=text_color,
                  font=(font, other_text_size), text='Cue Name').pack()
            self.custom_name_entry.pack()

        def add_cue_clicked(device):
            if device['type'] == 'nk_scpa_ip2sl':
                self._add_nk_scpa_ip2sl_cue(device)
            elif device['type'] == 'pvp':
                self._add_pvp_cue(device)
            elif device['type'] == 'ross_carbonite':
                if 'cc_labels' in device.keys():
                    cc_labels = ReadSheet(device['cc_labels']).read_cc_sheet()
                else:
                    cc_labels = None
                self._add_carbonite_cue(device, cc_labels=cc_labels)
            elif device['type'] == 'resi':
                self._add_resi_cue(device)
            elif device['type'] == 'ez_outlet_2':
                self._add_ez_outlet_2(device)
            elif device['type'] == 'bem104':
                self._add_bem104(device)
            elif device['type'] == 'controlflex':
                self._add_controlflex(device)
            elif device['type'] == 'aja_kumo':
                self._add_aja_kumo(device)
            elif device['type'] == 'ah_dlive':
                self._add__ah_dlive(device)
            elif device['type'] == 'midi':
                self._add_midi(device)
            elif device['type'] == 'obs':
                self._add_obs(device)
            elif device['type'] == 'propresenter':
                self._add_propresenter(device)
            elif device['type'] == 'webostv':
                self._add_webos_tv(device)
            elif device['type'] == 'wakeonlan':
                self._add_wakeonlan(device)

        # if the device is not pause, reminder, or kipro, create a button for it. Also looks to see if a kipro exists
        # will not create a button for each kipro, but will instead create a button to control ALL kipros, or 1, if
        # necessary.
        if self.devices is not None:
            for device in self.devices:
                if not device['type'] in ('pause', 'reminder', 'kipro', 'shure_qlxd'):
                    button_name = 'Add ' + device['user_name'] + '(' + device['type'] + ')' + ' cue'
                    Button(self.devices_buttons_frame, text=button_name, font=(font, options_button_text_size),
                           bg=bg_color, fg=text_color, command=lambda device=device: add_cue_clicked(device)).pack(
                        padx=10)
                elif device['type'] == 'kipro' and not device['user_name'] == 'All Kipros':
                    self.includes_kipro = True

        # see above comment
        if self.includes_kipro:
            Button(self.devices_buttons_frame, text='Add Kipro Cue', font=(font, options_button_text_size), bg=bg_color,
                   fg=text_color, command=self._add_kipro_cue).pack(padx=20)

        # Add pause/reminder button
        Button(self.devices_buttons_frame, text='Add Pause', font=(font, options_button_text_size), bg=bg_color,
               fg=text_color, command=self._add_pause_cue_clicked).pack(padx=20)
        Button(self.devices_buttons_frame, text='Add Reminder', font=(font, options_button_text_size), bg=bg_color,
               fg=text_color, command=self._add_reminder_cue_clicked).pack(padx=20)

        Button(self.cue_presets_button_frame, text='Delete a Cue Preset', font=(font, options_button_text_size),
               bg=bg_color, fg=text_color, command=self._remove_cue_preset_button_pressed).pack(pady=30)

        self._create_cue_preset_buttons()


        # Bottom buttons
        Button(self.bottom_buttons_frame, text='Save', font=(font, 11), bg=bg_color,
               fg=text_color, command=self._save).grid(row=1, column=0)
        Button(self.bottom_buttons_frame, text='Cancel', font=(font, 11), bg=bg_color, fg=text_color,
               command=lambda: self._cancel()).grid(row=1, column=1, padx=(0, 20))

        Button(self.bottom_buttons_frame, text='Test', font=(font, 11), bg=bg_color, fg=text_color,
               command=self._test).grid(row=1, column=2)
        Button(self.bottom_buttons_frame, text='Copy cues from a plan item', font=(font, 11),
               bg=bg_color, fg=text_color, command=lambda: self._copy_cues_from_plan_item()).grid(row=1, column=3)
        Button(self.bottom_buttons_frame, text='Remove Selected', font=(font, 11), bg=bg_color,
               fg=text_color, command=lambda: self._remove_selected()).grid(row=1, column=4)
        Button(self.bottom_buttons_frame, text='Remove All', font=(font, 11), bg=bg_color,
               fg=text_color, command=lambda: self._remove_all()).grid(row=1, column=5)

        Button(self.bottom_buttons_frame, text='Create Preset from Added Cues', font=(font, 11),
               bg=bg_color, fg=text_color, command=lambda: self._create_preset_from_added_cues()).grid(row=1, column=7)

        self._update_cues_display()

        self.cue_creator_window.mainloop()

    def _check_cues_for_errors(self) -> None:
        """
        Check the list of currently added cues for errors, such as if a device is offline or if a cue in pvp
        doesn't exist.
        If there is an error, color the listbox item red
        :return:
        """

        cues_valid_result = self.cue_handler.cues_are_valid(cuelist=self.current_cues['action_cues'])

        for i, cue in enumerate(cues_valid_result):
            if False in cue.keys():
                listboxitem_name = self.current_cues_listbox.get(i)
                self.current_cues_listbox.delete(i)

                self.current_cues_listbox.insert(i, f'{listboxitem_name}: {cue[False]}')
                self.current_cues_listbox.itemconfigure(i, bg=live_color)

    def _add_preset_button_clicked(self, preset: dict) -> None:
        """
        Callback for preset buttons. Should be called when button is clicked. Adds cues from button to cue creator.

        :param preset: Preset data in {'name': 'Joel Sims', 'cues': [{'uuid':
        '0763d390-aa2d-4802-ac81-cef1787abda3', 'playlist_uuid': 'FAF493A1-731F-4EBC-9041-191EC3544E85',
        'cue_uuid': 'BD7578E1-E022-43CA-A6DD-9A14223524F5', 'cue_name': 'JoelSims_V'}], 'uuid':
        'b1fdc7a4-08ec-4027-9f3e-c5368276feec'} format.
        :return: None.
        """
        logger.debug('Add preset button clicked: %s', preset)
        for cue in preset['cues']:
            self.current_cues['action_cues'].append(cue)
        self._update_cues_display()

    def _create_cue_preset_buttons(self) -> None:
        """
        Read cue_presets.json and create a button for each preset. Can be run multiple times in the case of a refresh.
        :return: None.
        """

        logger.debug('Creating cue preset buttons')

        self.cue_presets = self._try_read_cue_presets()

        if len(self.cue_preset_buttons) > 0:
            for button in self.cue_preset_buttons:
                button.destroy()
        self.cue_preset_buttons.clear()

        if self.cue_presets is not None:
            logger.debug('Cue presets is not none')
            for iteration, preset in enumerate(self.cue_presets):
                button = Button(self.cue_presets_button_frame, text=preset['name'], font=(font, options_button_text_size),
                       bg=bg_color, fg=text_color, command=lambda preset=preset: self._add_preset_button_clicked(preset))

                self.cue_preset_buttons.append(button)

            for button in self.cue_preset_buttons:
                button.pack(padx=20)

    def _move_selected_cue_up(self) -> None:
        """
        Moves a selected cue_index cue up one place in the user facing cuelist.

        :return: None
        """
        cue_index = self.current_cues_listbox.curselection()[0]

        logger.debug('Moving selected cue up: index %s', cue_index)
        cue_1 = self.current_cues['action_cues'][cue_index - 1]
        cue_2 = self.current_cues['action_cues'][cue_index]

        self.current_cues['action_cues'][cue_index] = cue_1
        self.current_cues['action_cues'][cue_index - 1] = cue_2

        self._update_cues_display()

        self.current_cues_listbox.select_set(cue_index-1)

    def _move_selected_cue_down(self) -> None:
        """
        Moves a selected cue_index cue down one place in the user facing cuelist.

        :return: None.
        """

        cue_index = self.current_cues_listbox.curselection()[0]

        logger.debug('Moving selected cue down: index %s', cue_index)
        cue_1 = self.current_cues['action_cues'][cue_index]
        cue_2 = self.current_cues['action_cues'][cue_index + 1]

        self.current_cues['action_cues'][cue_index] = cue_2
        self.current_cues['action_cues'][cue_index + 1] = cue_1

        self._update_cues_display()

        self.current_cues_listbox.select_set(cue_index+1)

    def _remove_cue_preset_button_pressed(self) -> None:
        """
        Open a window that gives user the opportunity to remove a cue preset. Upon removal, cue_presets.json
        file is updated and ui is refreshed.
        :return: None.
        """

        remove_cue_preset_window = Tk()
        remove_cue_preset_window.configure(bg=bg_color)
        listbox = Listbox(remove_cue_preset_window, bg=bg_color, fg=text_color, font=(font, other_text_size))
        listbox.pack()

        for iteration, item in enumerate(self.cue_presets):
            name = item['name']
            listbox.insert(iteration, name)

        def remove(index: int) -> None:
            self.cue_presets.pop(index)
            with open(os.path.join('configs', 'cue_presets.json'), 'w') as f:
                f.write(json.dumps(self.cue_presets))

            self._create_cue_preset_buttons()
            remove_cue_preset_window.destroy()

        Button(remove_cue_preset_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Delete',
               command=lambda: remove(listbox.curselection()[0])).pack(side=LEFT)
        Button(remove_cue_preset_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Cancel',
               command=lambda: remove_cue_preset_window.destroy()).pack(side=RIGHT)

    # --------------ADD _ CUE FUNCTIONS-----------------

    def _add_nk_scpa_ip2sl_cue(self, device):
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
                input_label = f"{str(input)}:  {input_labels[input - 1]}"
            else:
                input_label = f"Input {str(input)}"

            inputs_buttons.append(Radiobutton(inputs_frame,
                                              bg=bg_color,
                                              selectcolor=bg_color,
                                              fg=text_color, font=(font, other_text_size - 2),
                                              text=input_label,
                                              variable=selected_input,
                                              value=input))

        for iteration, button in enumerate(inputs_buttons):
            row = math.floor(iteration / 6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        #  outputs radiobuttons

        outputs_frame = Frame(add_nk_cue, bg=bg_color)
        outputs_buttons = []

        selected_output = IntVar(outputs_frame)

        def show_current_route():
            current_route = ScpaViaIP2SL(ip=device['ip_address']).get_status(output=selected_output.get())
            if current_route != 0:
                inputs_buttons[current_route - 1].flash()
                inputs_buttons[current_route - 1].select()

        for output in range(1, int(total_outputs) + 1):
            if has_labels:
                output_label = f"{str(output)}: {output_labels[output - 1]}"
            else:
                output_label = f"Output {str(output)}"

            outputs_buttons.append(Radiobutton(outputs_frame,
                                               bg=bg_color,
                                               fg=text_color,
                                               selectcolor=bg_color,
                                               font=(font, other_text_size - 2),
                                               text=output_label,
                                               variable=selected_output,
                                               value=output,
                                               command=show_current_route))

        for iteration, button in enumerate(outputs_buttons):
            row = math.floor(iteration / 6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        def add():
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'input': selected_input.get(),
                'output': selected_output.get()
            })

            self._update_cues_display()
            add_nk_cue.destroy()

        okay = Button(add_nk_cue, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Cue', command=add)

        outputs_frame.pack(anchor='w', pady=20)
        inputs_frame.pack(anchor='w', pady=20)
        okay.pack()

    def _add_pvp_cue(self, device):
        add_pvp_cue_window = Tk()
        add_pvp_cue_window.config(bg=bg_color)
        pvp_init = PVP(ip=device['ip_address'], port=device['port'])

        pvp_data = pvp_init.get_pvp_playlists()
        pvp_layers = pvp_init.get_pvp_layers()['data']

        add_trigger_cue_frame = Frame(add_pvp_cue_window, bg=secondary_bg_color)
        add_action_cue_frame = Frame(add_pvp_cue_window, bg=secondary_bg_color)

        add_trigger_cue_frame.pack(side=LEFT, padx=10, pady=10)
        add_action_cue_frame.pack(side=LEFT, padx=10, pady=10)

        Label(add_trigger_cue_frame, bg=secondary_bg_color, fg=text_color, font=(font, 12), text='Trigger Media').pack(
            pady=10)
        Label(add_action_cue_frame, bg=secondary_bg_color, fg=text_color, font=(font, 12),
              text='Layer/Workspace Actions').pack(pady=10)


        playlist_names = []
        for playlist in pvp_data['playlist']['children']:
            playlist_names.append(playlist['name'] + '...')

        playlist_buttons = []
        for iteration, playlist in enumerate(playlist_names):
            playlist_buttons.append(Button(add_trigger_cue_frame,
                                           text=playlist,
                                           font=(font, 11),
                                           bg=bg_color,
                                           fg=text_color,
                                           command=lambda iteration=iteration:
                                           (playlist_button_clicked(playlist_index=iteration),
                                            add_pvp_cue_window.destroy())))
        for button in playlist_buttons:
            button.pack()

        def playlist_button_clicked(playlist_index):
            add_cue_button_window = Tk()
            add_cue_button_window.config(bg=bg_color)

            playlist_uuid = pvp_data['playlist']['children'][playlist_index]['uuid']

            cue_names = []
            for cue_name in pvp_data['playlist']['children'][playlist_index]['items']:
                cue_names.append(cue_name['name'])

            cue_uuids = []
            for cue_name in pvp_data['playlist']['children'][playlist_index]['items']:
                cue_uuids.append(cue_name['uuid'])

            cue_buttons = []
            for name, uuid in zip(cue_names, cue_uuids):
                cue_buttons.append(Button(add_cue_button_window,
                                          text=name,
                                          font=(font, 11),
                                          bg=bg_color,
                                          fg=text_color,
                                          command=lambda uuid=uuid:
                                          (
                                              cue_button_clicked(cue_uuid=uuid,
                                                                 playlist_uuid=playlist_uuid),
                                              add_cue_button_window.destroy())))

            for button in cue_buttons:
                button.pack()

            def cue_button_clicked(cue_uuid, playlist_uuid):
                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'playlist_uuid': playlist_uuid,
                    'cue_uuid': cue_uuid,
                    'cue_type': 'cue_cue'
                })
                self._update_cues_display()

        def clear_button_clicked() -> None:
            add_pvp_cue_window.destroy()

            add_clear_button_window = Tk()
            add_clear_button_window.config(bg=bg_color)

            def clear_all_clicked() -> None:
                add_clear_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'clear_master'
                })
                self._update_cues_display()

            def clear_layer_clicked(layer_uuid) -> None:
                add_clear_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'clear_layer',
                    'layer_uuid': layer_uuid
                })
                self._update_cues_display()


            Button(add_clear_button_window, text='Clear Master', font=(font, 11), bg=bg_color, fg=text_color, command=clear_all_clicked).pack()
            Label(add_clear_button_window, text='Layers:', font=(font, 11), bg=bg_color, fg=text_color).pack()

            for layer in pvp_layers:
                Button(add_clear_button_window, text=layer['layer']['name'],
                       font=(font, 11),
                       bg=bg_color,
                       fg=text_color,
                       command=lambda layer=layer: clear_layer_clicked(layer_uuid=layer['layer']['uuid'])).pack()

        def mute_button_clicked() -> None:
            add_pvp_cue_window.destroy()

            add_mute_button_window = Tk()
            add_mute_button_window.config(bg=bg_color)

            def mute_all_clicked() -> None:
                add_mute_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'mute_master'
                })
                self._update_cues_display()

            def mute_layer_clicked(layer_uuid) -> None:
                add_mute_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'mute_layer',
                    'layer_uuid': layer_uuid
                })
                self._update_cues_display()

            Button(add_mute_button_window, text='Mute Master', font=(font, 11), bg=bg_color, fg=text_color,command=mute_all_clicked).pack()
            Label(add_mute_button_window, text='Layers:', font=(font, 11), bg=bg_color, fg=text_color).pack()

            for layer in pvp_layers:
                Button(add_mute_button_window, text=layer['layer']['name'],
                       font=(font, 11),
                       bg=bg_color,
                       fg=text_color,
                       command=lambda layer=layer: mute_layer_clicked(layer_uuid=layer['layer']['uuid'])).pack()


        def unmute_button_clicked() -> None:
            add_pvp_cue_window.destroy()

            add_unmute_button_window = Tk()
            add_unmute_button_window.config(bg=bg_color)

            def unmute_all_clicked() -> None:
                add_unmute_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'unmute_master'
                })
                self._update_cues_display()

            def unmute_layer_clicked(layer_uuid) -> None:
                add_unmute_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'unmute_layer',
                    'layer_uuid': layer_uuid
                })
                self._update_cues_display()

            Button(add_unmute_button_window, text='Unmute Master', font=(font, 11), bg=bg_color, fg=text_color,command=unmute_all_clicked).pack()
            Label(add_unmute_button_window, text='Layers:', font=(font, 11), bg=bg_color, fg=text_color).pack()

            for layer in pvp_layers:
                Button(add_unmute_button_window, text=layer['layer']['name'],
                       font=(font, 11),
                       bg=bg_color,
                       fg=text_color,
                       command=lambda layer=layer: unmute_layer_clicked(layer_uuid=layer['layer']['uuid'])).pack()

        def hide_button_clicked() -> None:
            add_pvp_cue_window.destroy()

            add_hide_button_window = Tk()
            add_hide_button_window.config(bg=bg_color)

            def hide_all_clicked() -> None:
                add_hide_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'hide_master'
                })
                self._update_cues_display()

            def hide_layer_clicked(layer_uuid) -> None:
                add_hide_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'hide_layer',
                    'layer_uuid': layer_uuid
                })
                self._update_cues_display()

            Button(add_hide_button_window, text='Hide Master', font=(font, 11), bg=bg_color, fg=text_color,command=hide_all_clicked).pack()
            Label(add_hide_button_window, text='Layers:', font=(font, 11), bg=bg_color, fg=text_color).pack()

            for layer in pvp_layers:
                Button(add_hide_button_window, text=layer['layer']['name'],
                       font=(font, 11),
                       bg=bg_color,
                       fg=text_color,
                       command=lambda layer=layer: hide_layer_clicked(layer_uuid=layer['layer']['uuid'])).pack()

        def unhide_button_clicked() -> None:
            add_pvp_cue_window.destroy()

            add_unhide_button_window = Tk()
            add_unhide_button_window.config(bg=bg_color)

            def unhide_all_clicked() -> None:
                add_unhide_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'unhide_master'
                })
                self._update_cues_display()

            def unhide_layer_clicked(layer_uuid) -> None:
                add_unhide_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'unhide_layer',
                    'layer_uuid': layer_uuid
                })
                self._update_cues_display()

            Button(add_unhide_button_window, text='Unhide Master', font=(font, 11), bg=bg_color, fg=text_color,command=unhide_all_clicked).pack()
            Label(add_unhide_button_window, text='Layers:', font=(font, 11), bg=bg_color, fg=text_color).pack()

            for layer in pvp_layers:
                Button(add_unhide_button_window, text=layer['layer']['name'],
                       font=(font, 11),
                       bg=bg_color,
                       fg=text_color,
                       command=lambda layer=layer: unhide_layer_clicked(layer_uuid=layer['layer']['uuid'])).pack()

        def pause_button_clicked() -> None:
            add_pvp_cue_window.destroy()

            add_pause_button_window = Tk()
            add_pause_button_window.config(bg=bg_color)

            def pause_all_clicked() -> None:
                add_pause_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'pause_master'
                })
                self._update_cues_display()

            def pause_layer_clicked(layer_uuid) -> None:
                add_pause_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'pause_layer',
                    'layer_uuid': layer_uuid
                })
                self._update_cues_display()

            Button(add_pause_button_window, text='Pause All', font=(font, 11), bg=bg_color, fg=text_color,command=pause_all_clicked).pack()
            Label(add_pause_button_window, text='Layers:', font=(font, 11), bg=bg_color, fg=text_color).pack()

            for layer in pvp_layers:
                Button(add_pause_button_window, text=layer['layer']['name'],
                       font=(font, 11),
                       bg=bg_color,
                       fg=text_color,
                       command=lambda layer=layer: pause_layer_clicked(layer_uuid=layer['layer']['uuid'])).pack()

        def unpause_button_clicked() -> None:
            add_pvp_cue_window.destroy()

            add_unpause_button_window = Tk()
            add_unpause_button_window.config(bg=bg_color)

            def unpause_all_clicked() -> None:
                add_unpause_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'unpause_master'
                })
                self._update_cues_display()

            def pause_layer_clicked(layer_uuid) -> None:
                add_unpause_button_window.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'cue_type': 'unpause_layer',
                    'layer_uuid': layer_uuid
                })
                self._update_cues_display()

            Button(add_unpause_button_window, text='Unpause Master', font=(font, 11), bg=bg_color, fg=text_color,command=unpause_all_clicked).pack()
            Label(add_unpause_button_window, text='Layers:', font=(font, 11), bg=bg_color, fg=text_color).pack()

            for layer in pvp_layers:
                Button(add_unpause_button_window, text=layer['layer']['name'],
                       font=(font, 11),
                       bg=bg_color,
                       fg=text_color,
                       command=lambda layer=layer: pause_layer_clicked(layer_uuid=layer['layer']['uuid'])).pack()


        Button(add_action_cue_frame, bg=bg_color, fg=text_color, font=(font, 11), text='Clear...', command=clear_button_clicked).pack()
        Button(add_action_cue_frame, bg=bg_color, fg=text_color, font=(font, 11), text='Mute...', command=mute_button_clicked).pack()
        Button(add_action_cue_frame, bg=bg_color, fg=text_color, font=(font, 11), text='Unmute...', command=unmute_button_clicked).pack()
        Button(add_action_cue_frame, bg=bg_color, fg=text_color, font=(font, 11), text='Hide...', command=hide_button_clicked).pack()
        Button(add_action_cue_frame, bg=bg_color, fg=text_color, font=(font, 11), text='Unhide...', command=unhide_button_clicked).pack()
        Button(add_action_cue_frame, bg=bg_color, fg=text_color, font=(font, 11), text='Pause...', command=pause_button_clicked).pack()
        Button(add_action_cue_frame, bg=bg_color, fg=text_color, font=(font, 11), text='Unpause...', command=unpause_button_clicked).pack()

    def _add_resi_cue(self, device):
        add_resi_cue_window = Tk()
        add_resi_cue_window.config(bg=bg_color)

        def button_pressed(command):
            add_resi_cue_window.destroy()
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'name': commands[command]['name'],
                'command': commands[command]['command']
            })
            self._update_cues_display()

        commands = {
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
                                       command=lambda iteration=iteration: button_pressed(command=iteration)))
        for button in resi_buttons:
            button.pack()

    def _add_carbonite_cue(self, device: dict, cc_labels):
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
                            new_title = 'CC ' + str(pos) + ': ' + label
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
                                         command=lambda bank=bank: update_cc_names(bank_int=bank + 1),
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

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'type': 'CC',
                    'bank': bank,
                    'CC': CC
                })
                self._update_cues_display()

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

    def _add_kipro_cue(self):
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
            self.current_cues['action_cues'].append({
                'start': start,
                'uuid': kipros[kipro]['uuid'],
                'name': kipros[kipro]['name']
            })
            add_kipro_cue_window.destroy()
            self._update_cues_display()

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
                                             command=lambda kipro=kipro: logger.debug('kipro button pressed: %s',
                                                                                      kipro['name'])))
        for radiobutton in kipro_buttons:
            radiobutton.pack()

            Button(add_kipro_cue_window,
                   text='okay',
                   bg=bg_color,
                   fg=text_color,
                   font=(font, plan_text_size),
                   command=okay_pressed).grid(row=1, column=0)

    def _add_ez_outlet_2(self, device):
        add_ez_outlet_cue_window = Tk()
        add_ez_outlet_cue_window.configure(bg=bg_color)

        command_selected = StringVar(add_ez_outlet_cue_window, value=None)

        def okay_pressed():
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'action': command_selected.get()
            })
            logger.debug('CueCreator.__add_ez_outlet_2 pressed. uuid %s, action %s', device['uuid'], command_selected)
            self._update_cues_display()
            add_ez_outlet_cue_window.destroy()

        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size),
                    text='Turn Outlet Off', selectcolor=bg_color, variable=command_selected, value='turn_off').pack()
        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size),
                    text='Turn Outlet On', selectcolor=bg_color, variable=command_selected, value='turn_on').pack()
        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size),
                    text='Toggle Outlet State', selectcolor=bg_color, variable=command_selected,
                    value='toggle_state').pack()
        Radiobutton(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size),
                    text='Reset Outlet', selectcolor=bg_color, variable=command_selected, value='reset').pack()
        Button(add_ez_outlet_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add',
               command=okay_pressed).pack()

    def _add_bem104(self, device):
        add_bem104_cue_window = Tk()
        add_bem104_cue_window.configure(bg=bg_color)

        relay_selected = StringVar(add_bem104_cue_window, value=None)
        command_selected = StringVar(add_bem104_cue_window, value=None)

        left_frame = Frame(add_bem104_cue_window, bg=bg_color)
        left_frame.grid(row=0, column=0)

        right_frame = Frame(add_bem104_cue_window, bg=bg_color)
        right_frame.grid(row=0, column=1)

        Radiobutton(left_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Relay 1',
                    selectcolor=bg_color, variable=relay_selected, value='1').pack()
        Radiobutton(left_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Relay 2',
                    selectcolor=bg_color, variable=relay_selected, value='2').pack()

        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Switch OFF',
                    selectcolor=bg_color, variable=command_selected, value='switch_off').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Switch ON',
                    selectcolor=bg_color, variable=command_selected, value='switch_on').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Toggle State',
                    selectcolor=bg_color, variable=command_selected, value='toggle').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Pulse off/on/off',
                    selectcolor=bg_color, variable=command_selected, value='pulse_on').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Pulse on/off/on',
                    selectcolor=bg_color, variable=command_selected, value='pulse_off').pack()
        Radiobutton(right_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Pulse Toggle',
                    selectcolor=bg_color, variable=command_selected, value='pulse_toggle').pack()

        def okay_pressed():
            logger.debug('CueCreator.__add_bem104 pressed. uuid %s, relay: %s, action: %s', device['uuid'],
                         relay_selected.get(), command_selected.get())

            if relay_selected.get() in (None, '') or command_selected.get() in (None, ''):
                messagebox.showerror(title='Please select relay and command',
                                     message='Please select a relay number and command')

            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'relay': relay_selected.get(),
                'command': command_selected.get()
            })
            self._update_cues_display()
            add_bem104_cue_window.destroy()

        Button(add_bem104_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add',
               command=okay_pressed).grid(row=1, column=0)

    def _add_controlflex(self, device):
        add_controlflex = Tk()
        add_controlflex.configure(bg=bg_color)

        all_controlflex_zones = device['zones']

        contains_qsys = False
        for zone in device[
            'zones']:  # if a qsys device exists, contains_qsys is true. used later for separating qsys zones
            if zone['zone_type'] == 'qsys':
                contains_qsys = True
                break

        if contains_qsys:
            qsys_zones = []  # ALL qsys zones in controlflex.
            for zone in device['zones']:
                if zone['zone_type'] == 'qsys':
                    qsys_zones.append(zone)
            qsys_zone_types = []  # list of qsys zone categories
            for qsys_zone in qsys_zones:
                if not qsys_zone['qsys_zone_type'] in qsys_zone_types:
                    qsys_zone_types.append(qsys_zone['qsys_zone_type'])

        zone_types = []  # types of controlflex zones: qsys, sony pro bravia, lighting, etc
        for zone in device['zones']:
            if not zone['zone_type'] in zone_types:
                zone_types.append(zone['zone_type'])

        controlflex_zone_frames = []

        def zone_type_selected(zone):  # run when a controlflex zone is selected
            logger.debug('__add_controlflex: zone type selected: %s', zone)
            for frame in controlflex_zone_frames:  # destroy frames holding controlflex zones
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
                self.current_cues['action_cues'].append(to_add)
                self._update_cues_display()

                logger.debug('__add_controlflex: command completed: %s', to_add)

            if zone['zone_type'] == 'qsys':  # selected zone type is qsys
                if zone['qsys_zone_type'] == 'qsys_mute':
                    Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                           text=f'MUTE {zone["friendly_name"]}',
                           command=lambda: command_finished(command={'args': 'mute', 'value': '1'}, zone=zone)).pack()
                    Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                           text=f'UNMUTE {zone["friendly_name"]}',
                           command=lambda: command_finished(command={'args': 'mute', 'value': '0'}, zone=zone)).pack()

                if zone['qsys_zone_type'] == 'qsys_gain':
                    Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                          text=f'Set {zone["friendly_name"]} to ').pack(side=LEFT)
                    percent_entry = Entry(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                                          width=2)
                    percent_entry.pack(side=LEFT)
                    Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='%.').pack(
                        side=LEFT)

                    def ok():
                        command_finished(command={'args': 'gain', 'value': percent_entry.get()}, zone=zone)

                    Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay',
                           command=ok).pack(side=BOTTOM)

                if zone['qsys_zone_type'] == 'qsys_source':
                    def ok(source_index):
                        command_finished(command={'args': 'source', 'value': source_index}, zone=zone)

                    for iteration, input in enumerate(zone['friendly_input_names'], start=1):
                        Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                               text=f'{input}', command=lambda iteration=iteration: ok(source_index=iteration)).pack()

            if zone['zone_type'] == 'sony_pro_bravia':
                # power
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                      text=f'Set {zone["friendly_name"]} power ').grid(row=0, column=0)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='ON',
                       command=lambda: command_finished(command={'args': 'power', 'value': '1'}, zone=zone)).grid(row=0,
                                                                                                                  column=1)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='OFF',
                       command=lambda: command_finished(command={'args': 'power', 'value': '0'}, zone=zone)).grid(row=0,
                                                                                                                  column=2)

                # volume
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                      text=f'Set {zone["friendly_name"]} volume to ').grid(row=1, column=0)
                percent_entry = Entry(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                                      width=2)
                percent_entry.grid(row=1, column=1)
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='%').grid(
                    row=1, column=2)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay',
                       command=lambda: command_finished(command={'args': 'volume', 'value': percent_entry.get()},
                                                        zone=zone)).grid(row=1, column=3)

                # input
                Label(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                      text=f'Set {zone["friendly_name"]} input to :').grid(row=2, column=0)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Input 1',
                       command=lambda: command_finished(command={'args': 'input', 'value': '1'}, zone=zone)).grid(row=2,
                                                                                                                  column=1)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Input 2',
                       command=lambda: command_finished(command={'args': 'input', 'value': '2'}, zone=zone)).grid(row=2,
                                                                                                                  column=2)
                Button(zone_command_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Input 3',
                       command=lambda: command_finished(command={'args': 'input', 'value': '2'}, zone=zone)).grid(row=2,
                                                                                                                  column=3)

        for zone_type in zone_types:  # add a frame for each controlflex zone type. Sony bravia, qsys, etc
            zone_frame = Frame(add_controlflex, bg=bg_color)
            zone_frame.pack(side=LEFT, anchor='n', padx=40)
            controlflex_zone_frames.append(zone_frame)

            if zone_type == 'qsys':
                qsys_zone_frames = []
                for qsys_zone_type in qsys_zone_types:  # if type is qsys, create a frame for each qsys zone type. name will match index of zone type above in qsys_zone_types
                    frame = Frame(zone_frame, bg=bg_color)
                    qsys_zone_frames.append(frame)
                    frame.pack(pady=15, side=BOTTOM)
                    Label(frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=qsys_zone_type).pack()

            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=f'{zone_type}:').pack(
                padx=10, pady=2, side=TOP)  # create label for type of controlflex zone.

            for controlflex_zone in all_controlflex_zones:
                if controlflex_zone['zone_type'] == zone_type:  # separate controlflex zone devices into groups
                    if zone_type == 'qsys':
                        qsys_zone_frame = qsys_zone_frames[qsys_zone_types.index(controlflex_zone['qsys_zone_type'])]
                        Button(qsys_zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                               text=controlflex_zone['friendly_name'],
                               command=lambda controlflex_zone=controlflex_zone: zone_type_selected(
                                   controlflex_zone)).pack(padx=10, pady=2)
                    else:
                        Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                               text=controlflex_zone['friendly_name'],
                               command=lambda controlflex_zone=controlflex_zone: zone_type_selected(
                                   controlflex_zone)).pack(padx=10, pady=2)

            if zone_type == 'sony_pro_bravia':
                Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                       text='All Sony Pro Bravias', command=lambda zone_type=zone_type: zone_type_selected(
                        {'zone_type': 'all_sony_pro_bravias'})).pack(padx=10, pady=10)

    def _add_aja_kumo(self, device):
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
                                              fg=text_color, font=(font, other_text_size - 2),
                                              text=input,
                                              variable=selected_input,
                                              value=iteration))

        for iteration, button in enumerate(inputs_buttons):
            row = math.floor(iteration / 6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        outputs_frame = Frame(add_kumo, bg=bg_color)

        selected_output = IntVar(outputs_frame)
        selected_output.set(value=1)

        outputs_buttons = []

        def show_current_route():
            current_route = kumo_api.get_route_from_dest(selected_output.get())
            inputs_buttons[current_route - 1].flash()
            inputs_buttons[current_route - 1].select()

        for iteration, output in enumerate(output_names, start=1):
            if output is None:
                output = f'Output {iteration}'

            outputs_buttons.append(Radiobutton(outputs_frame,
                                               bg=bg_color,
                                               fg=text_color,
                                               selectcolor=bg_color,
                                               font=(font, other_text_size - 2),
                                               text=output,
                                               variable=selected_output,
                                               value=iteration,
                                               command=show_current_route))

        for iteration, button in enumerate(outputs_buttons):
            row = math.floor(iteration / 6)
            column = iteration % 6
            button.grid(row=row, column=column, sticky='w')

        def add():
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'input': selected_input.get(),
                'output': selected_output.get()
            })

            self._update_cues_display()
            add_kumo.destroy()

        okay = Button(add_kumo, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Cue', command=add)

        outputs_frame.pack(anchor='w', padx=20, pady=10)
        inputs_frame.pack(anchor='w', padx=20, pady=10)
        okay.pack()

    def _add__ah_dlive(self, device):
        add_dlive_cue = Tk()
        add_dlive_cue.configure(bg=bg_color)

        Label(add_dlive_cue, text='Go to scene # (1-500):', bg=bg_color, fg=text_color,
              font=(font, other_text_size)).pack(side=LEFT)
        scene_entry = Entry(add_dlive_cue, width=3, bg=text_entry_box_bg_color, fg=text_color,
                            font=(font, other_text_size))
        scene_entry.pack(side=LEFT)

        def add():
            scene_entry_result = scene_entry.get()

            def error_box():
                messagebox.showerror(title='Invalid Scene Number',
                                     message='An invalid scene number was enterd: ' + scene_entry_result)
                logger.error('cue_creator.__add_ah_dlive: invalid scene number was entered: %s', scene_entry_result)
                add_dlive_cue.lift()

            try:
                if int(scene_entry_result) < 1 or int(scene_entry_result) > 500:
                    error_box()
                else:
                    self.current_cues['action_cues'].append({
                        'uuid': device['uuid'],
                        'scene_number': scene_entry_result
                    })
                    self._update_cues_display()
                    add_dlive_cue.destroy()

            except ValueError:
                scene_entry.delete(0, END)
                error_box()

        Button(add_dlive_cue, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=add).pack()

    def _add_midi(self, device):
        add_midi_cue = Tk()
        add_midi_cue.configure(bg=bg_color)

        if device['midi_type'] == 'ProPresenter':

            Label(add_midi_cue, text=f'MIDI for session {device["midi_device"]}', bg=bg_color, fg=text_color,
                  font=(font, 12)).grid(row=0, column=1, pady=10, sticky='n')
            Label(add_midi_cue,
                  text='(note: the commands below will only work if you autofill starting with 0 in the ProPresenter MIDI map.\nUse "custom midi" below if your mapping is not set to default.)',
                  bg=bg_color, fg=text_color, font=(font, 9)).grid(row=1, column=1, pady=10, sticky='n')

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

            clear_commands_frame = Frame(add_midi_cue)
            clear_commands_frame.configure(bg=secondary_bg_color)
            clear_commands_frame.grid(row=2, column=0, padx=10, pady=10)

            video_controls_frame = Frame(add_midi_cue)
            video_controls_frame.configure(bg=secondary_bg_color)
            video_controls_frame.grid(row=2, column=1, padx=10, pady=10)

            presentation_actions_frame = Frame(add_midi_cue)
            presentation_actions_frame.configure(bg=secondary_bg_color)
            presentation_actions_frame.grid(row=2, column=2, padx=10, pady=10)

            index_actions_frame = Frame(add_midi_cue)
            index_actions_frame.configure(bg=secondary_bg_color)
            index_actions_frame.grid(row=3, column=1, padx=10, pady=10)

            custom_action_frame = Frame(add_midi_cue)
            custom_action_frame.configure(bg=secondary_bg_color)
            custom_action_frame.grid(row=4, column=1, padx=10, pady=10)

            Label(clear_commands_frame, text='Clear Commands', bg=secondary_bg_color, fg=text_color,
                  font=(font, 11)).grid(row=0, column=0, pady=10, sticky='w')
            Label(video_controls_frame, text='Video Controls', bg=secondary_bg_color, fg=text_color,
                  font=(font, 11)).grid(row=0, column=0, pady=10, sticky='w')
            Label(presentation_actions_frame, text='Presentation Actions', bg=secondary_bg_color, fg=text_color,
                  font=(font, 11)).grid(row=0, column=0, pady=10, sticky='w')
            Label(index_actions_frame, text='Select by Index', bg=secondary_bg_color, fg=text_color,
                  font=(font, 11)).grid(row=0, column=0, pady=10, sticky='w')
            Label(index_actions_frame, text='#', bg=secondary_bg_color, fg=text_color, font=(font, 11)).grid(row=0,
                                                                                                             column=1,
                                                                                                             pady=10,
                                                                                                             sticky='e')
            Label(custom_action_frame, text='Custom Midi', bg=secondary_bg_color, fg=text_color, font=(font, 11)).grid(
                row=0, column=1, pady=10, sticky='w')

            clear_command_radiobuttons = []
            video_controls_radiobuttons = []
            presentation_actions_radiobuttons = []
            index_actions_radiobuttons = []
            index_actions_entries = []

            selected_command_var = StringVar(add_midi_cue)
            selected_command_var.set(clear_commands[0])

            for iteration, command in enumerate(clear_commands):
                r = Radiobutton(clear_commands_frame, variable=selected_command_var, value=command, text=command,
                                bg=secondary_bg_color, selectcolor=bg_color, fg=text_color, font=(font, 10))
                r.grid(row=iteration + 1, column=0, sticky='w')
                clear_command_radiobuttons.append(r)

            for iteration, command in enumerate(video_controls):
                r = Radiobutton(video_controls_frame, variable=selected_command_var, value=command, text=command,
                                bg=secondary_bg_color, selectcolor=bg_color, fg=text_color, font=(font, 10))
                r.grid(row=iteration + 1, column=0, sticky='w')
                video_controls_radiobuttons.append(r)

            for iteration, command in enumerate(presentation_actions):
                r = Radiobutton(presentation_actions_frame, variable=selected_command_var, value=command, text=command,
                                bg=secondary_bg_color, selectcolor=bg_color, fg=text_color, font=(font, 10))
                r.grid(row=iteration + 1, column=0, sticky='w')
                presentation_actions_radiobuttons.append(r)

            for iteration, command in enumerate(index_actions):
                r = Radiobutton(index_actions_frame, variable=selected_command_var, value=command, text=command,
                                bg=secondary_bg_color, selectcolor=bg_color, fg=text_color, font=(font, 10))
                r.grid(row=iteration + 1, column=0, sticky='w')
                index_actions_radiobuttons.append(r)

                e = Entry(index_actions_frame, bg=secondary_bg_color, fg=text_color, font=(font, 10), width=3)
                e.grid(row=iteration + 1, column=1, sticky='w')
                e.insert(index=0, string='1')
                index_actions_entries.append(e)

            Radiobutton(custom_action_frame, variable=selected_command_var, value='custom', text='',
                        bg=secondary_bg_color, selectcolor=bg_color, fg=text_color, font=(font, 10)).grid(row=1,
                                                                                                          column=0)

            custom_channel_entry: Entry = Entry(custom_action_frame, bg=secondary_bg_color, fg=text_color,
                                                font=(font, 10), width=3)
            custom_channel_entry.insert(index=0, string='0')
            custom_note_entry = Entry(custom_action_frame, bg=secondary_bg_color, fg=text_color, font=(font, 10),
                                      width=3)
            custom_velocity_entry = Entry(custom_action_frame, bg=secondary_bg_color, fg=text_color, font=(font, 10),
                                          width=3)

            custom_channel_entry.grid(row=1, column=2)
            custom_note_entry.grid(row=1, column=4)
            custom_velocity_entry.grid(row=1, column=6)

            Label(custom_action_frame, text='Channel (default 0): ', bg=secondary_bg_color, fg=text_color,
                  font=(font, 10)).grid(row=1, column=1, pady=10, sticky='e')
            Label(custom_action_frame, text='Note: ', bg=secondary_bg_color, fg=text_color, font=(font, 10)).grid(row=1,
                                                                                                                  column=3,
                                                                                                                  pady=10,
                                                                                                                  sticky='e')
            Label(custom_action_frame, text='Velocity: ', bg=secondary_bg_color, fg=text_color, font=(font, 10)).grid(
                row=1, column=5, pady=10, sticky='e')

            def add():
                all_lists = [clear_commands, video_controls, presentation_actions, index_actions]

                is_index = False
                user_cue_index = None

                def add_and_update(cue):
                    self.current_cues['action_cues'].append(cue)
                    self._update_cues_display()
                    add_midi_cue.destroy()

                for list in all_lists:
                    for command in list:
                        if command == selected_command_var.get():
                            if command in index_actions:
                                entry_index = index_actions.index(command)
                                user_cue_index = index_actions_entries[entry_index].get()
                                is_index = True

                if is_index:
                    logger.debug('Adding propresenter midi cue: %s, index %s', selected_command_var.get(),
                                 user_cue_index)
                    try:
                        int(user_cue_index)
                        to_add = {
                            'uuid': device['uuid'],
                            'command': selected_command_var.get(),
                            'index': int(user_cue_index)
                        }
                        add_and_update(to_add)

                    except ValueError:  # user did not type an index in
                        messagebox.showerror(title='Error',
                                             message=f'Please enter an index for item {selected_command_var.get()}')

                if selected_command_var.get() == 'custom':

                    def show_error():
                        messagebox.showerror(title='Error',
                                             message=f'Invalid channel, note, or velocity entered.\nChannels must be 0-15, Notes: 0-128, Velocity: 0-127')

                    try:

                        if int(custom_channel_entry.get()) < 0 or int(custom_channel_entry.get()) > 15:
                            show_error()

                        if int(custom_note_entry.get()) < 0 or int(custom_note_entry.get()) > 127:
                            show_error()

                        if int(custom_velocity_entry.get()) < 0 or int(custom_velocity_entry.get()) > 127:
                            show_error()

                        else:
                            to_add = {
                                'uuid': device['uuid'],
                                'command': selected_command_var.get(),
                                'channel': int(custom_channel_entry.get()),
                                'note': int(custom_note_entry.get()),
                                'velocity': int(custom_velocity_entry.get())
                            }

                            add_and_update(to_add)

                    except ValueError:  # user didn't fill out all custom fields or entered an invalid character
                        show_error()

                elif not is_index:
                    logger.debug('Adding propresenter midi cue: %s', selected_command_var.get())
                    to_add = {
                        'uuid': device['uuid'],
                        'command': selected_command_var.get()
                    }

                    add_and_update(to_add)

            Button(add_midi_cue, bg=bg_color, fg=text_color, text='Add', command=add, font=(font, 13)).grid(row=5,
                                                                                                            column=1,
                                                                                                            pady=10)

        if device['midi_type'] == 'Other/Custom':

            custom_action_frame = Frame(add_midi_cue)
            custom_action_frame.configure(bg=secondary_bg_color)
            custom_action_frame.grid(row=2, column=1, padx=10, pady=10)

            Label(custom_action_frame, text=f'Custom Midi on session {device["midi_device"]}', bg=secondary_bg_color,
                  fg=text_color, font=(font, 11)).grid(row=0, column=1, pady=10, sticky='w')

            custom_channel_entry: Entry = Entry(custom_action_frame, bg=secondary_bg_color, fg=text_color,
                                                font=(font, 10), width=3)
            custom_channel_entry.insert(index=0, string='0')
            custom_note_entry = Entry(custom_action_frame, bg=secondary_bg_color, fg=text_color, font=(font, 10),
                                      width=3)
            custom_velocity_entry = Entry(custom_action_frame, bg=secondary_bg_color, fg=text_color, font=(font, 10),
                                          width=3)

            custom_channel_entry.grid(row=1, column=2)
            custom_note_entry.grid(row=1, column=4)
            custom_velocity_entry.grid(row=1, column=6)

            Label(custom_action_frame, text='Channel (default 0): ', bg=secondary_bg_color, fg=text_color,
                  font=(font, 10)).grid(row=1, column=1, pady=10, sticky='e')
            Label(custom_action_frame, text='Note: ', bg=secondary_bg_color, fg=text_color, font=(font, 10)).grid(row=1,
                                                                                                                  column=3,
                                                                                                                  pady=10,
                                                                                                                  sticky='e')
            Label(custom_action_frame, text='Velocity: ', bg=secondary_bg_color, fg=text_color, font=(font, 10)).grid(
                row=1, column=5, pady=10, sticky='e')

            def add():
                def show_error():
                    messagebox.showerror(title='Error',
                                         message=f'Invalid channel, note, or velocity entered.\nChannels must be 0-15, Notes: 0-128, Velocity: 0-127')

                try:
                    if int(custom_channel_entry.get()) < 0 or int(custom_channel_entry.get()) > 15:
                        show_error()

                    if int(custom_note_entry.get()) < 0 or int(custom_note_entry.get()) > 127:
                        show_error()

                    if int(custom_velocity_entry.get()) < 0 or int(custom_velocity_entry.get()) > 127:
                        show_error()

                    else:
                        to_add = {
                            'uuid': device['uuid'],
                            'channel': int(custom_channel_entry.get()),
                            'note': int(custom_note_entry.get()),
                            'velocity': int(custom_velocity_entry.get())
                        }

                        self.current_cues['action_cues'].append(to_add)
                        self._update_cues_display()
                        add_midi_cue.destroy()

                except ValueError:  # user didn't fill out all custom fields or entered an invalid character
                    show_error()

            Button(add_midi_cue, bg=bg_color, fg=text_color, text='Add', command=add, font=(font, 13)).grid(row=3,
                                                                                                            column=1,
                                                                                                            pady=10)

    def _add_obs(self, device):
        add_obs_cue = Tk()
        add_obs_cue.configure(bg=bg_color)

        def add(value):
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'command': value
            })
            self._update_cues_display()
            add_obs_cue.destroy()

        start_recording = Button(add_obs_cue, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                                 anchor='w', justify='left', text='Start Recording',
                                 command=lambda: add('start_recording'))

        stop_recording = Button(add_obs_cue, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                                anchor='w', justify='left', text='Stop Recording',
                                command=lambda: add('stop_recording'))

        start_recording.grid(row=0, column=0)
        stop_recording.grid(row=1, column=0)

    def _add_propresenter(self, device):
        pp = ProPresenter(ip=device['ip_address'], port=device['port'])
        macros = pp.get_macros()

        add_propresenter = Tk()
        add_propresenter.configure(bg=bg_color)

        if not pp.is_online():
            add_propresenter.destroy()
            messagebox.showerror("Offline!", message=f"Propresenter machine at {device['ip_address']} is offline.")

        # Convert RGB values from Propresenter macros to hex values for use later
        def rgb_to_hex(red: float, green: float, blue: float) -> str:
            red = int(red*255)
            green = int(green*255)
            blue = int(blue*255)
            return "#{:02X}{:02X}{:02X}".format(red, green, blue)

        def add_macro_button_clicked():
            def macro_button_clicked(macro):
                add_macro.destroy()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'command_type': 'trigger_macro',
                    'macro_uuid': macro['id']['uuid']
                })
                self._update_cues_display()

            add_propresenter.destroy()

            add_macro = Tk()
            add_macro.configure(bg=bg_color)

            for i, macro in enumerate(macros):
                Button(add_macro, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                       text=macro['id']['name'], command=lambda macro=macro: macro_button_clicked(macro)).grid(row=i, column=1)
                macro_color = macro['color']

                frame_bg_color = rgb_to_hex(red=macro_color['red'], green=macro_color['green'], blue=macro_color['blue'])
                Frame(add_macro, bg=frame_bg_color, width=5).grid(row=i, column=0, sticky='news')

        def show_stage_display_message_clicked():
            def okay():
                stage_message_text: str = stage_message_entry.get()

                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'command_type': 'show_stage_display_message',
                    'stage_display_message': stage_message_text
                })
                self._update_cues_display()

                show_stage_display_message.destroy()

            add_propresenter.destroy()

            show_stage_display_message = Tk()
            show_stage_display_message.configure(bg=bg_color)

            Label(show_stage_display_message, text='Your stage display message:', bg=bg_color, fg=text_color, font=(font, current_cues_text_size)).pack()

            stage_message_entry = Entry(show_stage_display_message, width=100, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
            stage_message_entry.pack(pady=5)

            Button(show_stage_display_message, text='Okay', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), command=okay).pack(pady=5)

        def hide_stage_display_message_clicked():
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'command_type': 'hide_stage_display_message'
            })

            self._update_cues_display()
            add_propresenter.destroy()

        add_macro_button = Button(add_propresenter, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                                  text='Add Macro Cue', command=add_macro_button_clicked)
        show_stage_display_message = Button(add_propresenter, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                                  text='Show a stage display message', command=show_stage_display_message_clicked)
        hide_stage_display_message = Button(add_propresenter, bg=bg_color, fg=text_color, font=(font, plan_text_size),
                                            text='Hide current stage display message', command=hide_stage_display_message_clicked)

        add_macro_button.pack()
        show_stage_display_message.pack()
        hide_stage_display_message.pack()

    def _add_webos_tv(self, device):
        tv = WebOSTV(device['ip_address'])

        add_webos_tv = Tk()
        add_webos_tv.configure(bg=bg_color)

        if not tv.is_online():
            add_webos_tv.destroy()
            messagebox.showerror("Offline!", message=f"TV at {device['ip_address']} is offline.")
            add_webos_tv.destroy()

        inputs = tv.get_inputs()

        # inputs
        def switch_input(input: dict) -> None:
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'command_type': 'change_to_input',
                'input_id': input['id'],
                'input_label': input['label']
            })
            self._update_cues_display()
            add_webos_tv.destroy()

        input_frame = Frame(add_webos_tv, bg=bg_color)

        Label(input_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
              text='Switch to input:').grid(row=0, column=0)

        for i, input in enumerate(inputs):
            Button(input_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
                   text=input['label'], command=lambda i=i: switch_input(inputs[i])).grid(row=0, column=i+1, sticky='w')

        input_frame.grid(row=0, column=0, sticky='w', pady=5)

        # volume
        volume_frame = Frame(add_webos_tv, bg=bg_color)

        def set_volume():
            def set():
                self.current_cues['action_cues'].append({
                    'uuid': device['uuid'],
                    'command_type': 'set_volume',
                    'volume': int(volume_input.get())
                })
                self._update_cues_display()
                add_webos_tv.destroy()

            try:
                volume_input_result = int(volume_input.get()) # this may result in ValueError if user entered something other than an int
                if volume_input_result > 100 or volume_input_result < 0:
                    messagebox.showerror("Invalid!", message=f"Please enter a number between 0 - 100.")
                else:
                    set()
            except ValueError:
                messagebox.showerror("Invalid!", message=f"Volume value entered is invalid.")
                add_webos_tv.lift()

        Label(volume_frame, text='Set volume to: ', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w').grid(row=0, column=0)

        volume_input = Entry(volume_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), width=3)
        volume_input.grid(row=0, column=1)

        set_volume_button = Button(volume_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
                            text='Set', command=set_volume)
        set_volume_button.grid(row=0, column=2)

        volume_frame.grid(row=1, column=0, sticky='w', pady=5)

        # mute
        mute_frame = Frame(add_webos_tv, bg=bg_color)

        def mute_state(state: bool) -> None:
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'command_type': 'mute',
                'state': state
            })
            self._update_cues_display()
            add_webos_tv.destroy()

        Label(mute_frame, text='Set mute state to:', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w').grid(row=0, column=0)
        Button(mute_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', text='Mute', command=lambda: mute_state(True)).grid(row=0, column=1, sticky='w')
        Button(mute_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', text='Unmute', command=lambda: mute_state(False)).grid(row=0, column=2, sticky='w')

        mute_frame.grid(row=2, column=0, sticky='w', pady=5)

        # Power
        power_frame = Frame(add_webos_tv, bg=bg_color)

        def power_off() -> None:
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'command_type': 'power_off'
            })
            self._update_cues_display()
            add_webos_tv.destroy()

        Button(power_frame, text='Power Off', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=power_off).grid(row=0, column=0, sticky='w')
        Label(power_frame, text='Power on is issued through Wake On Lan', bg=bg_color, fg=text_color, font=(font, current_cues_text_size - 2), anchor='w').grid(row=1, column=0, columnspan=1)

        power_frame.grid(row=3, column=0, sticky='w', pady=5)

        # press button
        press_button_frame = Frame(add_webos_tv, bg=bg_color)

        def button_press(button_id: str, button_name: str) -> None:
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
                'command_type': 'press_button',
                'button_id': button_id,
                'button_name': button_name
            })
            self._update_cues_display()
            add_webos_tv.destroy()

        Button(press_button_frame, text='Press "UP" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('UP', 'UP')).grid(row=0, column=0)
        Button(press_button_frame, text='Press "DOWN" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('DOWN', 'DOWN')).grid(row=1, column=0)
        Button(press_button_frame, text='Press "LEFT" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('LEFT', 'LEFT')).grid(row=2, column=0)
        Button(press_button_frame, text='Press "RIGHT" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('RIGHT', 'RIGHT')).grid(row=3, column=0)
        Button(press_button_frame, text='Press "RED" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('RED', 'RED')).grid(row=4, column=0)
        Button(press_button_frame, text='Press "GREEN" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('GREEN', 'GREEN')).grid(row=5, column=0)
        Button(press_button_frame, text='Press "YELLOW" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('YELLOW', 'YELLOW')).grid(row=6, column=0)
        Button(press_button_frame, text='Press "BLUE" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('BLUE', 'BLUE')).grid(row=7, column=0)
        Button(press_button_frame, text='Press "CHANNEL UP" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('CHANNELUP', 'CHANNEL UP')).grid(row=8, column=0)
        Button(press_button_frame, text='Press "CHANNEL DOWN" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('CHANNELDOWN', "CHANNEL DOWN")).grid(row=9, column=0)
        Button(press_button_frame, text='Press "VOLUME UP" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('VOLUMEUP', "VOLUME UP")).grid(row=10, column=0)
        Button(press_button_frame, text='Press "VOLUME DOWN" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('VOLUMEDOWN', 'VOLUME DOWN')).grid(row=11, column=0)
        Button(press_button_frame, text='Press "PLAY" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('PLAY', 'PLAY')).grid(row=12, column=0)
        Button(press_button_frame, text='Press "PAUSE" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('PAUSE', "PAUSE")).grid(row=13, column=0)
        Button(press_button_frame, text='Press "STOP" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('STOP', "STOP")).grid(row=14, column=0)
        Button(press_button_frame, text='Press "REWIND" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('REWIND', 'REWIND')).grid(row=15, column=0)
        Button(press_button_frame, text='Press "FAST FORWARD" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('FASTFORWARD', "FAST FORWARD")).grid(row=16, column=0)
        Button(press_button_frame, text='Press "BACK" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('BACK', 'BACK')).grid(row=17, column=0)
        Button(press_button_frame, text='Press "EXIT" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('EXIT', "EXIT")).grid(row=18, column=0)
        Button(press_button_frame, text='Press "ENTER" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('ENTER', 'ENTER')).grid(row=19, column=0)
        Button(press_button_frame, text='Press "ADVANCE SETTING" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('ADVANCE_SETTING', 'ADVANCE SETTING')).grid(row=20, column=0)
        Button(press_button_frame, text='Press "CLOSED CAPTIONS" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('CC', 'CLOSED CAPTIONS')).grid(row=21, column=0)
        Button(press_button_frame, text='Press "HOME" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('HOME', 'HOME')).grid(row=22, column=0)
        Button(press_button_frame, text='Press "INFO" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('INFO', 'INFO')).grid(row=23, column=0)
        Button(press_button_frame, text='Press "MENU" button', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w', command=lambda: button_press('MENU', "MENU")).grid(row=24, column=0)

        press_button_frame.grid(row=4, column=0, sticky='w', pady=6)

    def _add_wakeonlan(self, device):
        add_wakeonlan = Tk()
        add_wakeonlan.configure(bg=bg_color)

        def add():
            self.current_cues['action_cues'].append({
                'uuid': device['uuid'],
            })
            self._update_cues_display()
            add_wakeonlan.destroy()

        Button(add_wakeonlan, bg=bg_color, fg=text_color, font=(font, plan_text_size), text=f'{device["user_name"]}: Send Wake On Lan Packet', command=add).pack()

    def _add_reminder_cue_clicked(self):
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

            self.current_cues['action_cues'].append({
                'uuid': reminder_uuid,
                'device': 'reminder',
                'minutes': int(minutes),
                'seconds': int(seconds),
                'reminder': str(reminder)
            })
            self._update_cues_display()

            logger.debug('Okay button pressed on add_reminder_window. Minutes: %s, '
                         'Seconds: %s, Str: %s', minutes, seconds, reminder)
            add_reminder_window.destroy()

        time_entry_frame = Frame(add_reminder_window)
        time_entry_frame.config(bg=bg_color)
        time_entry_frame.grid(row=1, column=0)

        Label(add_reminder_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
              text='Add reminder after x time:').grid(row=0, column=0)

        Label(time_entry_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
              text='Add reminder in: ').grid(row=1, column=0)

        minutes_entry = Entry(time_entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                              font=(font, current_cues_text_size))
        minutes_entry.grid(row=1, column=2)

        Label(time_entry_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
              text='minutes, ').grid(row=1, column=3)

        seconds_entry = Entry(time_entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                              font=(font, current_cues_text_size))
        seconds_entry.grid(row=1, column=4)

        Label(time_entry_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
              text='seconds.').grid(row=1, column=5)

        reminder_entry = Entry(add_reminder_window, width=100, bg=text_entry_box_bg_color, fg=text_color,
                               font=(font, plan_text_size))
        reminder_entry.grid(row=2, column=0)

        Button(add_reminder_window, bg=bg_color, fg=text_color, font=(font, plan_text_size), anchor='w', text='okay',
               command=okay_pressed).grid(row=3, column=0)

    def _add_pause_cue_clicked(self):
        add_pause_window = Tk()
        add_pause_window.config(bg=bg_color)

        add_pause_for_x_seconds = Label(add_pause_window, bg=bg_color, fg=text_color,
                                        font=(font, current_cues_text_size),
                                        anchor='w', justify='left', text='Add pause for ___ seconds:')
        add_pause_for_x_seconds.grid(row=0, column=0)

        seconds = [.25, .5, .75, 1, 2, 3, 5, 10, 30, 60, 90, 120]

        for iteration, x in enumerate(seconds):
            seconds_button = Button(add_pause_window, bg=bg_color, fg=text_color, font=(font, plan_text_size-2),
                                    anchor='w', justify='left', text=f'{x} Seconds',
                                    command=lambda x=x: (add_pause_button_clicked(seconds=x)))
            seconds_button.grid(row=1, column=iteration)

        # also add an input for an exact number of seconds that need to be waited
        Label(add_pause_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size), anchor='w',
              justify='left', text='Custom:').grid(row=1, column=len(seconds) + 1)
        input_text = Text(add_pause_window, bg=bg_color, fg=text_color, font=(font, plan_text_size), width=5, height=1)
        input_text.grid(row=1, column=len(seconds) + 2)

        def add_custom():
            user_input = input_text.get('1.0', END)
            try:
                add_pause_button_clicked(float(user_input))
            except ValueError: # user entered something non-valid, clear it
                input_text.delete("1.0", "end")

        Button(add_pause_window, bg=bg_color, fg=text_color, font=(font, plan_text_size), anchor='w', justify='left',
               text='add', command=add_custom).grid(row=1, column=len(seconds) + 3)

        def add_pause_button_clicked(seconds):
            self.current_cues['action_cues'].append({
                'uuid': 'f0d73b84-60b1-4c1d-a49f-f3b11ea65d3f',
                'device': 'pause',
                'time': seconds
            })
            add_pause_window.destroy()
            self._update_cues_display()

    def _add_advance_cue(self):
        add_advance_window = Tk()
        add_advance_window.config(bg=bg_color)

        description_frame = Frame(add_advance_window, bg=bg_color)
        description_frame.pack()

        advance_description = Label(description_frame, bg=bg_color, fg=text_color,
                                    font=(font, current_cues_text_size),
                                    anchor='w', justify='left',
                                    text='Advance to the next item at a certain time, ONLY if current item is still live. Multiple times can be entered if you have more than 1 service.\nPress "Add Time" to add another entry and "Okay" when you are finished.')
        advance_description.grid(row=0, column=0)

        entry_frame = Frame(add_advance_window, bg=bg_color)
        entry_frame.pack()

        total_times = 0

        hours_entries = []
        minutes_entries = []
        seconds_entries = []

        # adds an additional line for the user to enter another advance time
        def add_advance_time():
            nonlocal total_times
            total_times += 1

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=f'Advance to next item at       ').grid(row=total_times, column=0)

            hours_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                font=(font, current_cues_text_size + 1))
            hours_entry.grid(row=total_times, column=1)
            hours_entries.append(hours_entry)

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=':').grid(row=total_times, column=2)

            minutes_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                  font=(font, current_cues_text_size + 1))
            minutes_entry.grid(row=total_times, column=3)
            minutes_entries.append(minutes_entry)

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=':').grid(row=total_times, column=4)

            seconds_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                  font=(font, current_cues_text_size + 1))
            seconds_entry.grid(row=total_times, column=5)
            seconds_entries.append(seconds_entry)

        # this actually adds the advance cue data
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

            for advance_time in times:
                self.current_cues.advance_to_next_on_time.append(advance_time)

            self._update_cues_display()
            add_advance_window.destroy()

        Button(add_advance_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size + 2), text='Add time',
               command=add_advance_time).pack()
        Button(add_advance_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size + 2), text='Okay',
               command=okay_pressed).pack()

    # ----------BOTTOM BUTTON FUNCTIONS----------

    def _save(self) -> None:
        """
        Writes cues to PCO, closes this window, and updates main ui window.
        :return: None
        """

        self.cue_creator_window.withdraw()

        if self.type_of_cues_being_edited == 'item':
            if bool(self.update_item_length.get()):

                seconds = int(self.update_minutes.get())*60 + int(self.update_seconds.get())
                self.pco_plan.update_plan_item_length(item_id=self.input_item['id'], length=seconds)

            # update auto advance to next cue in main current_cues dict
            self.current_cues['advance_to_next_automatically'] = self.auto_advance_to_next.get()

            self.pco_plan.create_and_update_item_app_cue(item_id=self.input_item['id'],
                                                         app_cue=json.dumps(self.current_cues))
            self.main_ui.update_items_view()

        if self.type_of_cues_being_edited == 'plan':
            cue_name = self.custom_name_entry.get()
            custom_cue_set = self.current_cues

            if self.is_editing_plan_cue:
                self.imported_plan_cues[self.plan_cue_index_being_edited] = [cue_name, custom_cue_set]
            else:
                self.imported_plan_cues.append([cue_name, custom_cue_set])

            self.pco_plan.create_and_update_plan_app_cues(app_cue=json.dumps(self.imported_plan_cues))
            self.main_ui.update_plan_cues()

        if self.type_of_cues_being_edited == 'global':
            self.global_cues[self.global_cue_bank_being_edited][self.global_cue_index_being_edited]['name'] = self.custom_name_entry.get()
            self.global_cues[self.global_cue_bank_being_edited][self.global_cue_index_being_edited]['cues'] = self.current_cues['action_cues']

            with open(os.path.join('configs', 'global_cues.json'), 'w') as f:
                f.write(json.dumps(self.global_cues))

            self.global_cue_shotbox_init._reload()

        self.cue_creator_window.destroy()


    def _cancel(self) -> None:
        """
        Closes main cue creator window.
        :return: None
        """
        self.cue_creator_window.destroy()

    def _test(self) -> None:
        """
        Run the cues currently in the cuelist.
        :return: None
        """

        logger.debug('Testing current cues')

        threading.Thread(target=self.cue_handler.activate_cues, kwargs={'cuelist':self.current_cues['action_cues']}).start()

    def _copy_cues_from_plan_item(self) -> None:
        """
        Copy cues from a different plan item that exists anywhere on PCO. Will open a service type>service picker.
        :return: None.
        """

        from_plan = SelectService(send_to=self)
        from_plan.ask_service_info()

    def _remove_selected(self):
        logger.debug('Removing selected item: %s',
                     self.current_cues['action_cues'][self.current_cues_listbox.curselection()[0]])
        self.current_cues['action_cues'].pop(self.current_cues_listbox.curselection()[0])
        self.current_cues_listbox.delete(self.current_cues_listbox.curselection()[0])

        self._update_cues_display()

    def _remove_all(self):
        self.current_cues['action_cues'].clear()
        self._update_cues_display()

    def _schedule_advance_to_next(self) -> None:
        """
        Opens new window to schedule an advance to next at a particular time.

        :return: None.
        """

        add_advance_window = Tk()
        add_advance_window.config(bg=bg_color)

        description_frame = Frame(add_advance_window, bg=bg_color)
        description_frame.pack()

        advance_description = Label(description_frame, bg=bg_color, fg=text_color,
                                    font=(font, current_cues_text_size),
                                    anchor='w', justify='left', text='Advance to the next item at a certain time, '
                                                                     'ONLY if current item is still live. Multiple '
                                                                     'times can be entered if you have more than 1 '
                                                                     'service.\nPress "Add Time" to add another entry '
                                                                     'and "Okay" when you are finished.')
        advance_description.grid(row=0, column=0)

        entry_frame = Frame(add_advance_window, bg=bg_color)
        entry_frame.pack()

        total_times = 0

        hours_entries = []
        minutes_entries = []
        seconds_entries = []

        # adds a line for the user to enter another advance time
        def add_advance_time():
            nonlocal total_times
            total_times += 1

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=f'Advance to next item at       ').grid(row=total_times, column=0)

            hours_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                font=(font, current_cues_text_size + 1))
            hours_entry.grid(row=total_times, column=1)
            hours_entries.append(hours_entry)

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=':').grid(row=total_times, column=2)

            minutes_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                  font=(font, current_cues_text_size + 1))
            minutes_entry.grid(row=total_times, column=3)
            minutes_entries.append(minutes_entry)

            Label(entry_frame, bg=bg_color, fg=text_color,
                  font=(font, current_cues_text_size),
                  anchor='w', justify='left', text=':').grid(row=total_times, column=4)

            seconds_entry = Entry(entry_frame, width=2, bg=text_entry_box_bg_color, fg=text_color,
                                  font=(font, current_cues_text_size + 1))
            seconds_entry.grid(row=total_times, column=5)
            seconds_entries.append(seconds_entry)

        # this actually adds the advance cue data
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

            for advance_time in times:
                self.current_cues['advance_to_next_on_time'].append(advance_time)

            self._update_cues_display()
            add_advance_window.destroy()

        add_advance_time()

        Button(add_advance_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size + 2),
               text='Add another time', command=add_advance_time).pack()
        Button(add_advance_window, bg=bg_color, fg=text_color, font=(font, current_cues_text_size + 2),
               text='Okay', command=okay_pressed).pack()

    def _create_preset_from_added_cues(self):  # create preset with currently added cues
        create_preset_window = Tk()
        create_preset_window.geometry('800x100')
        create_preset_window.configure(bg=bg_color)

        Label(create_preset_window, text='Create a preset with currently added cues. Preset name:',
              font=(font, other_text_size), bg=bg_color, fg=text_color).pack()
        preset_name_entry = Entry(create_preset_window, font=(font, other_text_size), bg=bg_color, fg=text_color,
                                  width=75)
        preset_name_entry.pack()

        def add():  # add button clicked
            cues = []
            for cue in self.current_cues['action_cues']:
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

                with open(os.path.join('configs', 'cue_presets.json'), 'w') as f:
                    f.write(json.dumps(cue_presets))

            else:
                with open(os.path.join('configs', 'cue_presets.json'), 'w') as f:
                    logger.debug('cue_presets.json exists, appending')

                    current_cue_presets = self.cue_presets
                    current_cue_presets.append(to_append)
                    f.write(json.dumps(current_cue_presets))

            create_preset_window.destroy()
            self._create_cue_preset_buttons()

        Button(create_preset_window, text='Add Preset', font=(font, other_text_size), bg=bg_color, fg=text_color,
               command=add).pack()

    @staticmethod
    def _try_read_cue_presets() -> Union[list, None]:
        """
        Attempt to read cue presets at configs/cue_presets.json

        :return: list of cue presets., None if file was not found or unable to decode
        """

        if os.path.exists(os.path.join('configs', 'cue_presets.json')):
            try:
                with open(os.path.join('configs', 'cue_presets.json'), 'r') as f:
                    logger.debug('Read cue_presets.json.')
                    return json.loads(f.read())
            except json.decoder.JSONDecodeError:
                logger.error('Unable to read json on cue_presets.json, returning None')
                return None
        return None


if __name__ == '__main__':
    with open(os.path.join('configs', 'devices.json'), 'r') as f:
        devices = json.loads(f.read())


    class FakeMain:
        def __init__(self):
            self.service_type_id = 0
            self.service_id = 0


    class FakeUI:
        def __init__(self):
            self.fake: None
            self.pco_plan = PcoPlan()


    fake_main = FakeMain()
    fake_ui = FakeUI()

    fake_input_item = {'title': 'Pre-Service Playlist', 'type': 'item', 'length': 1500, 'service_position': 'pre',
                       'id': '824628067', 'sequence': 4, 'notes': {'Stage': 'clear', 'Video': 'Pre-Service Media'}}

    cc = CueCreator(startup=fake_main, ui=fake_ui, devices=devices)
    # cc.create_plan_item_cue(input_item=fake_input_item)
    cc.create_plan_cue(cuelist=[])