# try:
import _tkinter
from tkinter import *
from tkinter import messagebox

import logzero
import urllib3.exceptions

import flask_server
from configs.settings import *
import time
from logzero import logfile
from typing import List

from cue_handler import CueHandler
from pco_plan import PcoPlan
from pco_live import PcoLive
from tkinter import ttk
import threading
from cue_creator import CueCreator
import json
import os
from kipro import KiPro
from rosstalk import rosstalk as rt
from sheet_reader import *
from device_editor import DeviceEditor
from select_service import SelectService
import datetime as dt
import math
from shure_qlxd_async import ShureQLXD
import multiprocessing as mp
import logging
from global_cues import GlobalCues
from typing import List, Dict
import webbrowser
from persistent_plan_data import PersistentPlanData
from sound_check_mode_options import SoundCheckModeOptions

abs_path = os.path.dirname(__file__)

# logging: absolute paths
if not os.path.exists(os.path.join(abs_path, 'logs')):
    os.mkdir(os.path.join(abs_path, 'logs'))

log_file_name = os.path.join(os.path.join(abs_path, 'logs'), time.strftime('%Y_%m_%d__%H_%M') + '.log')
logfile(log_file_name)

logging.getLogger('urllib3').setLevel(logging.INFO)


# main utilities menu under settings gear at top of plan window
class UtilitiesMenu:
    def __init__(self, main_ui_window_init, startup):
        self.startup = startup
        self.main_ui_window = main_ui_window_init
        self.cue_handler = main_ui_window_init.cue_handler

        self.pco_live = PcoLive(service_type_id = self.main_ui_window.service_type_id, plan_id=self.main_ui_window.service_id)
        self.pco_plan = PcoPlan(service_type = self.main_ui_window.service_type_id, plan_id=self.main_ui_window.service_id)

        self.utilities_menu = Tk()

        self.contains_kipro = False

        for device in self.startup.devices:
            if device['type'] == 'kipro' and device['uuid'] != all_kipros_uuid:
                self.contains_kipro = True

        self.kipro = KiPro()


        self.sound_check_mode_frame = Frame(self.utilities_menu, bg=bg_color)
        self.sound_check_checkbutton_value = IntVar(self.sound_check_mode_frame)
        self.sound_check_mode_checkbutton = Checkbutton(self.sound_check_mode_frame, bg=bg_color, variable=self.sound_check_checkbutton_value,command=lambda: self._sound_check_mode_checked(bool(self.sound_check_checkbutton_value.get())))

        self.delay_advance_to_next_schedule_frame = Frame(self.utilities_menu, bg=bg_color)


    def open_utilities_menu(self):
        self.utilities_menu.configure(bg=bg_color)

        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Advance to Next Service', font=(font, other_text_size), command=self._advance_to_next_service).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Add Plan Cue', font=(font, other_text_size), command=self._add_plan_cue).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Edit Plan Cue', font=(font, other_text_size), command=self._edit_plan_cue).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Remove Plan Cue', font=(font, other_text_size), command=self._remove_plan_cue).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Open Device Editor', font=(font, other_text_size), command=self._open_device_editor).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Hard Reload App', font=(font, other_text_size), command=self._hard_reload_app).pack()

        if self.contains_kipro:
            Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Format Kipros', font=(font, other_text_size), command=self._format_kipros).pack()
            Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Download Kipro Clips', font=(font, other_text_size), command=self._download_kipro_clips).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Update switcher cam names from PCO positions (Lakeland)', font=(font, other_text_size), command=self._update_cam_names).pack()

        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Open PCO plan in browser', font=(font, other_text_size), command=self._open_pco_plan_in_browser).pack()

        self.sound_check_mode_frame.pack()
        self.sound_check_mode_checkbutton.grid(row=0, column=0)
        Label(self.sound_check_mode_frame, text='Sound Check Mode', bg=bg_color, fg=text_color,font=(font, other_text_size)).grid(row=0, column=1)
        Button(self.sound_check_mode_frame, text='options', bg=bg_color, fg=text_color, command=lambda: SoundCheckModeOptions().open_sound_check_mode_options_menu()).grid(row=0, column=2, padx=5)

        self.delay_advance_to_next_schedule_frame.pack()
        Label(self.delay_advance_to_next_schedule_frame, text='Delay Advance To Next Schedule By:', bg=bg_color, fg=text_color,font=(font, other_text_size)).grid(row=0, column=1)

        delay_minutes_entry = Entry(self.delay_advance_to_next_schedule_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), width=3)
        delay_minutes_entry.grid(row=0, column=2)
        delay_minutes_entry.insert(0, '00')

        Label(self.delay_advance_to_next_schedule_frame, text=':', bg=bg_color, fg=text_color, font=(font, other_text_size)).grid(row=0, column=3)

        delay_seconds_entry = Entry(self.delay_advance_to_next_schedule_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), width=3, )
        delay_seconds_entry.grid(row=0, column=4)
        delay_seconds_entry.insert(0, '00')

        def delay_okay_pressed() -> int:
            """
            Called when user presses "set" on "delay advance to next" settings. Validates user input.
            :return: int of minutes + seconds
            """

            minutes_entered = delay_minutes_entry.get()
            seconds_entered = delay_seconds_entry.get()

            if minutes_entered == '':
                minutes_entered = 0
            if seconds_entered == '':
                seconds_entered = 0

            try:
                minutes = int(minutes_entered)
                seconds = int(seconds_entered)

                return minutes*60 + seconds
            except ValueError:  # User entered some garbage
                messagebox.showerror(title='Invalid Entry', message='You entered an invalid value')

                # clear entries and reset them back to their default values
                delay_minutes_entry.delete(0, len(minutes_entered))
                delay_seconds_entry.delete(0, len(seconds_entered))

                delay_minutes_entry.insert(0, '00')
                delay_seconds_entry.insert(0, '00')

                # Bring utilities menu back to front
                self.utilities_menu.lift()


        Button(self.delay_advance_to_next_schedule_frame, text='Set', bg=bg_color, fg=text_color, command=lambda: self._delay_advance_to_next_schedule(delay_okay_pressed())).grid(row=0, column=5)

        if self.main_ui_window.sound_check_mode:
            self.sound_check_mode_checkbutton.select()

        self.utilities_menu.mainloop()

    def _sound_check_mode_checked(self, status: bool) -> None:
        """
        Called when the sound check mode checkbutton is clicked by the user.
        :param status: status of the button
        :return: None
        """

        if status:
            self.main_ui_window.turn_sound_check_mode_on()
        else:
            self.main_ui_window.turn_sound_check_mode_off()

    def _delay_advance_to_next_schedule(self, seconds: int) -> None:
        """
        Called when the status of delay advance to next schedule checkbutton is clicked by the user.
        :param seconds: amount of seconds to delay
        :return: None
        """

        if seconds <= 0:
            pass
        else:
            self.main_ui_window.delay_advance_to_next_schedule(seconds)
            self.utilities_menu.destroy()


    def _open_device_editor(self):
        self.utilities_menu.destroy()
        DeviceEditor().build_ui()

    def _advance_to_next_service(self):
        # Set each frame and label in the plan items view back to its original bg color. For more info
        # on this absolute thicc boy, see the update_live function
        for frame, time_label, spacer_label, title_label, person_label, producer_note_label, app_cue_label, item in \
                zip(self.main_ui_window.item_frames, self.main_ui_window.item_time_labels, self.main_ui_window.item_spacer_labels,
                    self.main_ui_window.item_title_labels, self.main_ui_window.item_person_labels, self.main_ui_window.item_producer_note_labels,
                    self.main_ui_window.item_app_cue_labels, self.main_ui_window.plan_items):
            if not item['type'] == 'header':
                try:
                    frame.configure(bg=bg_color)
                except AttributeError:
                    pass
                try:
                    time_label.configure(bg=bg_color)
                except AttributeError:
                    pass
                try:
                    spacer_label.configure(bg=bg_color)
                except AttributeError:
                    pass
                try:
                    title_label.configure(bg=bg_color)
                except AttributeError:
                    pass
                try:
                    person_label.configure(bg=bg_color)
                except AttributeError:
                    pass
                try:
                    producer_note_label.configure(bg=bg_color)
                except AttributeError:
                    pass
                try:
                    app_cue_label.configure(bg=bg_color)
                except AttributeError:
                    pass


        self.pco_live.go_to_next_service()
        self.pco_live.go_to_previous_item()
        self.utilities_menu.destroy()

    def _format_kipros(self):
        yes_no = messagebox.askyesno('Format KiPros', message="Are you sure you want to format ALL KiPros?")
        if yes_no:
            for kipro_unit in self.main_ui_window.all_kipros:
                self.kipro.format_current_slot(ip=kipro_unit['ip_address'])

        self.utilities_menu.destroy()

    def _download_kipro_clips(self):
        """Download all clips from all kipros in devices file."""
        logger.debug('download kipro clips button pressed')
        self.utilities_menu.destroy()
        threading.Thread(target=self.kipro.download_clips).start()
        self.main_ui_window.kipro_ui.kill_threads()

    # Finds the FIRST ross carbonite device in the devices file to use, pulls people down from pco,
    # updates input mnemonics
    def _update_cam_names(self):
        people = self.pco_plan.get_assigned_people()

        for device in self.main_ui_window.startup.devices:
            if device['type'] == 'ross_carbonite':
                switcher_ip = device['ip_address']
                switcher_port = device['port']

        for person in people:
            cam_pos = None
            if person['position'].startswith('Cam') and person['status'] != 'D':
                for char in person['position'].split():
                    try:
                        cam_pos = int(char)
                    except Exception:
                        pass
            if cam_pos is not None:
                name = person['name'].upper()
                logger.debug('Updating camera position name via rosstalk: %s, %s', person['position'], name[0:6])
                rt(rosstalk_ip=switcher_ip, rosstalk_port=switcher_port, command=f"MNEM IN:{cam_pos}:{cam_pos} {name[0:6]}")

    def _add_plan_cue(self):
        self.utilities_menu.destroy()
        CueCreator(startup=self.startup, ui=self.main_ui_window, devices=self.startup.devices).create_plan_cue(cuelist=self.main_ui_window.plan_cues)

    def _edit_plan_cue(self):
        self.utilities_menu.destroy()
        logger.debug('Utilities._edit_plan_cue clicked.')
        if len(self.main_ui_window.plan_cues) > 0:
            current_plan_cues = self.main_ui_window.plan_cues

            edit_plan_cue_window = Tk()
            edit_plan_cue_window.configure(bg=bg_color)
            listbox = Listbox(edit_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size))
            listbox.pack()

            for iteration, item in enumerate(current_plan_cues):
                name = item[0]
                listbox.insert(iteration, name)

            def edit(index: int) -> None:
                logger.debug(f'_edit_plan_cue: editing item {current_plan_cues[index][0]}')
                edit_plan_cue_window.destroy()
                CueCreator(startup=self.startup, ui=self.main_ui_window, devices=self.startup.devices).edit_plan_cue(cuelist=self.main_ui_window.plan_cues, cue_index=index)

            Button(edit_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Edit',
                   command=lambda: edit(listbox.curselection()[0])).pack(side=LEFT)
            Button(edit_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Cancel',
                   command=lambda: edit_plan_cue_window.destroy()).pack(side=RIGHT)

    def _remove_plan_cue(self):
        logger.debug('Utilities.__remove_plan_cue clicked')
        self.utilities_menu.destroy()
        if len(self.main_ui_window.plan_cues) > 0:
            current_plan_cues = self.main_ui_window.plan_cues

            remove_plan_cue_window = Tk()
            remove_plan_cue_window.configure(bg=bg_color)
            listbox = Listbox(remove_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size))
            listbox.pack()

            for iteration, item in enumerate(current_plan_cues):
                name = item[0]
                listbox.insert(iteration, name)

            def okay():
                logger.debug('Utilities.__remove_plan: sending updated cues: %s', current_plan_cues)
                remove_plan_cue_window.destroy()
                self.pco_plan.create_and_update_plan_app_cues(app_cue=json.dumps(current_plan_cues))
                self.main_ui_window.update_plan_cues()

            Button(remove_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Remove',
                   command=lambda: (current_plan_cues.pop(listbox.curselection()[0]), listbox.delete(first=listbox.curselection()[0]))).pack(side=LEFT)
            Button(remove_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay',
                   command=okay).pack(side=RIGHT)

    def _remove_global_cue(self):
        logger.debug('Utilities.__remove_global_cue clicked')
        self.utilities_menu.destroy()

        global_cues = []

        with open(os.path.join('configs', 'global_cues.json'), 'r') as f:
            global_cues = json.loads(f.read())

        remove_global_cue_window = Tk()
        remove_global_cue_window.configure(bg=bg_color)
        listbox = Listbox(remove_global_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size))
        listbox.pack()

        for iteration, item in enumerate(global_cues):
            name = item[0]
            listbox.insert(iteration, name)

        def okay():
            logger.debug('Utilities.__remove_plan: sending updated cues: %s', global_cues)
            remove_global_cue_window.destroy()

            with open(os.path.join('configs', 'global_cues.json'), 'w') as f:
                f.writelines(json.dumps(global_cues))

            self.main_ui_window._reload()

        Button(remove_global_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Remove',
               command=lambda: (
               global_cues.pop(listbox.curselection()[0]), listbox.delete(first=listbox.curselection()[0]))).pack(
            side=LEFT)

        Button(remove_global_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay',
               command=okay).pack(side=RIGHT)

    def _hard_reload_app(self):
        self.utilities_menu.destroy()
        self.main_ui_window.reload()

    def _open_pco_plan_in_browser(self):
        logger.debug(f'{__class__.__name__}.{self._open_pco_plan_in_browser.__name__}')

        pco_plan_id: int = self.main_ui_window.service_id
        webbrowser.open(f'https://www.planningcenteronline.com/plans/{pco_plan_id}')
        self.utilities_menu.destroy()


class MainUI:
    def __init__(self, startup):
        self.startup = startup
        self.startup.has_started = True

        # service info
        self.service_type_id = self.startup.service_type_id
        self.service_id = self.startup.service_id

        # class initiations
        self.pco_live = PcoLive(service_type_id=self.service_type_id, plan_id=self.service_id)
        self.pco_plan = PcoPlan(service_type=self.service_type_id, plan_id=self.service_id)
        self.cue_handler = CueHandler(devices=startup.devices)
        self.kipro_ui = KiProUi()
        self.kipro = KiPro()
        self.qlxd = None

        self.plan_items = self.convert_service_items_app_cues_to_dict_and_validate(self.pco_plan.get_plan_items())
        self.pco_plan.include_all_items_in_live()

        self.previous_item_index = None
        self.current_item_index = 0  # index of the current live item
        self.next_item_index = None

        self.current_live_item_id = self.pco_live.get_current_live_item()

        # get + set index of current live item
        for item in self.plan_items:
            if item['id'] == self.current_live_item_id:
                self.current_item_index = item['sequence']

        # plan item timer
        self.time_remaining_is_positive = True
        self.current_item_timer_input = 60

        # plan window
        self.plan_window = Tk()

        # plan window frames
        self.reminder_frame = Frame(self.plan_window, bg=bg_color)
        self.clock_frame = Frame(self.plan_window, bg=bg_color)

        self.aux_controls_frame = Frame(self.plan_window, bg=bg_color)
        self.kipro_control_frame = Frame(self.plan_window, bg=bg_color)
        self.plan_cues_frame = Frame(self.plan_window, bg=bg_color)
        self.current_service_frame = Frame(self.plan_window, bg=bg_color)
        self.qlxd_frame = Frame(self.plan_window, bg=bg_color)

        self.service_controls_frame = Frame(self.plan_window, bg=bg_color)
        self.next_previous_frame = Frame(self.service_controls_frame, bg=bg_color)

        self.gear_icon = PhotoImage(file=os.path.join(abs_path, 'gear_icon_gray.png'))
        self.gear_icon = self.gear_icon.subsample(11, 11)

        self.update_items_view_icon = PhotoImage(file=os.path.join(abs_path, 'refresh_icon.png'))
        self.update_items_view_icon = self.update_items_view_icon.subsample(11, 11)

        self.cue_warning_icon = PhotoImage(file=os.path.join(abs_path, 'cue_warning_icon.png'))
        self.cue_warning_icon = self.cue_warning_icon.subsample(11, 11)

        self.item_frames = []
        self.item_time_labels = []
        self.item_spacer_labels = []
        self.separators = []
        self.item_title_labels = []
        self.item_person_labels = []
        self.item_producer_note_labels = []
        self.item_app_cue_labels = []
        self.item_advance_cue_labels = []
        self.item_advance_to_next_automatically_arrow_images = []

        # scrollbar for plan items frame (service_plan_frame)
        self.plan_items_canvas = Canvas(self.plan_window, bg=bg_color, width=plan_item_frame_width, height=plan_item_view_height, highlightthickness=0)
        self.items_view_scrollbar = None

        self.service_plan_frame = Frame(self.plan_items_canvas, bg=bg_color)

        self.plan_items_canvas.create_window(0, 0, anchor='nw', window=self.service_plan_frame)

        self.plan_items_canvas.grid(row=4, column=0)

        # height of all plan item frames added together
        self.service_plan_frame_height = None

        self.auto_advance_arrow_image = PhotoImage(file=os.path.join(abs_path, 'advance_to_next_arrow.png')).subsample(65, 65)

        self.auto_advance_automatically_cancelled_by_user = False

        self.auto_advance_on_time_cancelled_by_user = False
        self.auto_advance_reminder_frame = None
        self.auto_advance_reminder_label = None

        self.all_kipros = []
        if self.startup.devices is not None:
            for device in self.startup.devices:
                if device['type'] == 'kipro' and not device['uuid'] == '07af78bf-9149-4a12-80fc-0fa61abc0a5c':
                    self.all_kipros.append(device)

        self.kipro_buttons = []
        self.kipro_storage_remaining_bars = []

        self.plan_cues = []
        self.plan_cue_buttons: List[Button] = []

        self._build_global_cues_button()

        # this value should only be written by the below methods
        self.sound_check_mode: bool = False

        self.sound_check_mode_frame = Frame(self.plan_window)
        self.sound_check_mode_frame.configure(bg=accent_color_1)
        Label(self.sound_check_mode_frame, bg=accent_color_1, text='Sound check mode active!', font=(font, 11)).grid(row=0, column=0)
        Button(self.sound_check_mode_frame, text='Disable', bg=accent_color_1, font=(font, 11), command=self.turn_sound_check_mode_off).grid(row=0, column=1)

        #Use this to keep track of when the utilities menu unit. Close the existing one when user tries to open a new one.
        self.existing_utilities_init: UtilitiesMenu = None

        self.advance_to_next_schedule_has_been_delayed: bool = False
        self.advance_to_next_delay: int = 0

        self.advance_delay_frame = Frame(self.plan_window)
        self.advance_delay_frame.configure(bg=accent_color_1)
        self.advance_delay_label = Label(self.advance_delay_frame, bg=accent_color_1, font=(font, 11))
        self.advance_delay_label.grid(row=0, column=0)
        Button(self.advance_delay_frame, text='Disable', bg=accent_color_1, font=(font, 11), command=self._turn_off_delay_advance_to_next_schedule).grid(row=0, column=1)

    def turn_sound_check_mode_on(self) -> None:
        """
        Turn sound check mode on
        :return: None
        """
        self.sound_check_mode = True
        self.sound_check_mode_frame.grid(row=2, column=0, sticky='ew')

    def turn_sound_check_mode_off(self) -> None:
        """
        Turn sound check mode off
        :return: None
        """
        self.sound_check_mode = False
        self.sound_check_mode_frame.grid_remove()

        try:
            self.existing_utilities_init.sound_check_mode_checkbutton.deselect()
        except _tkinter.TclError:  # User closed utilities menu
            pass

    def delay_advance_to_next_schedule(self, seconds: int) -> None:
        """
        Delays all advance to next on time schedules by x seconds.
        :param seconds: Amount of seconds to delay
        :return: None
        """
        logger.info(f'{__class__.__name__}.{self.delay_advance_to_next_schedule.__name__}: Enabling delay advance to next schedule with {seconds} seconds.')

        self.advance_to_next_schedule_has_been_delayed = True
        self.advance_to_next_delay = seconds


        self.advance_delay_label.configure(text=f'Advance To Next Schedule Delayed by {time.strftime("%M:%S", time.gmtime(seconds))}')
        self.advance_delay_frame.grid(row=3, column=0, sticky='ew')

    def _turn_off_delay_advance_to_next_schedule(self) -> None:
        """
        Turn off the delay advance to next schedule
        :return: None
        """
        self.advance_to_next_schedule_has_been_delayed = False
        self.advance_to_next_delay = 0
        self.advance_delay_frame.grid_remove()

    def build_plan_window(self):
        self.plan_window.title('Service Control')
        self.plan_window.configure(bg=bg_color)

        #TODO update this when advancing to next service
        # self._build_current_service_time()
        self._build_auto_advance_reminder_ui()

        self._build_clock()
        self._build_item_timer()
        self._build_items_view()
        self._build_aux_control()

        # If a utilities menu is already open, kill it and reopen a new one, so only 1 instance is open at a time.
        def open_utilities_menu() -> None:
            try:
                self.existing_utilities_init.utilities_menu.destroy()
            except Exception as e:
                pass

            self.existing_utilities_init = UtilitiesMenu(main_ui_window_init=self, startup=self.startup)
            self.existing_utilities_init.open_utilities_menu()

            # if self.sound_check_mode:
            #     self.existing_utilities_init.


        # utilities menu button
        Button(self.clock_frame, bg=bg_color, image=self.gear_icon, command=open_utilities_menu).grid(row=0, column=2, padx=10)

        #refresh button
        Button(self.clock_frame, bg=bg_color, image=self.update_items_view_icon, command=self.update_items_view).grid(row=0, column=3, padx=10)

        if display_kipros:
            self._build_kipro_status()

        self._build_plan_cue_buttons()

        self.check_if_current_added_cues_and_devices_valid_and_online()

        self.update_live()

        threading.Thread(target=lambda: flask_server.start_flask_server(main_ui=self)).start()

        if self.startup.contains_qlxd:
            self._build_qlxd_ui()

        self._ui_cleanup()

        logger.debug('All running threads: %s', threading.enumerate())

        if __name__ == '__main__':
            mp.Process(target=self.plan_window.mainloop()).start()

    def update_item_timer(self, time_value):
        self.time_remaining_is_positive = True
        self.current_item_timer_input = time_value

    def next(self, cue_items, from_web=False):
        logger.debug('Next button pressed. Next item index: %s', self.next_item_index)

        self.auto_advance_on_time_cancelled_by_user = False
        self.auto_advance_automatically_cancelled_by_user = False


        if cue_items:
            self._cue()

        self.update_item_timer(time_value=self.plan_items[self.next_item_index]['length'])

        self.pco_live.go_to_next_item()
        self.update_live()

    def previous(self, cue_items, from_web=False):
        logger.debug('Previous button pressed. Previous item index: %s', self.previous_item_index)

        self.auto_advance_on_time_cancelled_by_user = False
        self.auto_advance_automatically_cancelled_by_user = False

        self.update_item_timer(time_value=self.plan_items[self.previous_item_index]['length'])

        if cue_items:
            self._cue(is_next=False)

        self.pco_live.go_to_previous_item()
        self.update_live()

    def update_live(self, service_time=False):
        # Get index of current live item
        self.current_live_item_id = self.pco_live.get_current_live_item()

        '''Colors CURRENT live item
        Normally, we would configure each label/frame item separately, but if the label doesn't exist for that item, the source list
        contains None. Adding None makes the index consistent across lists.
        Each action has it's own try/except loop, because if we configured all labels at the same time, a single exception
        would stop at the exception, skipping all labels after it'''

        for item in self.plan_items:
            if item['id'] == self.current_live_item_id:
                logger.debug('Current live item is index %s, %s', item['sequence'], item['title'])

                live_index = item['sequence']

                self.current_item_index = live_index

                labels_to_update = [
                    self.item_frames[item['sequence'] - 1],
                    self.item_time_labels[item['sequence'] - 1],
                    self.item_spacer_labels[item['sequence'] - 1],
                    self.item_title_labels[item['sequence'] - 1],
                    self.item_person_labels[item['sequence'] - 1],
                    self.item_producer_note_labels[item['sequence'] - 1],
                    self.item_app_cue_labels[item['sequence'] - 1],
                    self.item_advance_cue_labels[item['sequence'] - 1],
                    self.item_advance_to_next_automatically_arrow_images[item['sequence'] - 1]
                ]

                for label in labels_to_update:
                    try:
                        label.configure(bg=live_color)
                    except AttributeError:
                        pass

        def find_previous_item(i):
            if not self.plan_items[i-1]['type'] == 'header':
                logger.debug('__update_live: find_previous_item: returning %s', i)
                return i-1
            else:
                return find_previous_item(i-1)

        def find_next_item(i):
            try:
                if not self.plan_items[i+1]['type'] == 'header':
                    logger.debug('__update_live: find_next_item: returning %s', i)
                    return i+1
                else:
                    return find_next_item(i+1)
            except IndexError:
                if i > 0:
                    logger.debug('__update_live: find_next_item: reached end of plan')
                    return i
                else:
                    logger.debug('__update_live: find_next_item: plan may not be live')
                    return i

        def define_labels_to_change(index):
            labels = [
                self.item_frames[index],
                self.item_time_labels[index],
                self.item_spacer_labels[index],
                self.item_title_labels[index],
                self.item_person_labels[index],
                self.item_producer_note_labels[index],
                self.item_app_cue_labels[index],
                self.item_advance_cue_labels[index],
                self.item_advance_to_next_automatically_arrow_images[index]
            ]
            return labels

        is_first_item = False
        is_last_item = False

        if self.current_item_index == 1:
            logger.debug('Current live item is the first plan item, id %s', self.current_live_item_id)
            is_first_item = True

        if self.current_item_index == len(self.plan_items):
            logger.debug('Current live item is the last plan item, id %s', self.current_live_item_id)
            is_last_item = True

        self.previous_item_index = find_previous_item(self.current_item_index-1)
        self.next_item_index = find_next_item(self.current_item_index-1)

        if not is_first_item:
            for previous_item in define_labels_to_change(self.previous_item_index):
                try:
                    previous_item.configure(bg=bg_color)
                except AttributeError:
                    pass

        if not is_last_item:
            for next_item in define_labels_to_change(self.next_item_index):
                try:
                    next_item.configure(bg=bg_color)
                except AttributeError:
                    pass

        if service_time:
            self._build_current_service_time()

    def update_kipro_status(self, kipro_unit, status):
        # logger.debug('Got kipro status: unit: %s, status: %s', kipro_unit, status)
        try:
            if status == 1:
                self.kipro_buttons[kipro_unit].configure(bg=kipro_idle_color)
            elif status == 2:
                self.kipro_buttons[kipro_unit].configure(bg=kipro_recording_color)
            else:
                self.kipro_buttons[kipro_unit].configure(bg=kipro_error_color)
        except Exception as e: # plan window has been closed by user. Throws a _tkinter.Tclerror
            pass

    def update_kipro_storage(self, kipro_unit, percent):
        try:
            self.kipro_storage_remaining_bars[kipro_unit].configure(value=percent)
        except Exception as e: # plan window has been closed by user. Throws a _tkinter.Tclerror
            pass

    def update_items_view(self): # pulls all item data down from pco and reloads it into app without closing it
        logger.debug('Updating plan items view')

        self.plan_items = self.convert_service_items_app_cues_to_dict_and_validate(self.pco_plan.get_plan_items())

        self.pco_plan.include_all_items_in_live()

        for frame in self.item_frames:
            frame.destroy()

        for separator in self.separators:
            separator.destroy()

        self.item_time_labels.clear()
        self.item_spacer_labels.clear()
        self.separators.clear()
        self.item_title_labels.clear()
        self.item_person_labels.clear()
        self.item_producer_note_labels.clear()
        self.item_app_cue_labels.clear()
        self.item_advance_cue_labels.clear()
        self.item_frames.clear()
        self.item_advance_to_next_automatically_arrow_images.clear()

        self._build_items_view()

        self._ui_cleanup()

        self.update_live()

        self.update_plan_cues()

        threading.Thread(target=self.check_if_current_added_cues_and_devices_valid_and_online).start()

    def update_plan_cues(self):
        """
        :return:
        """

        if len(self.plan_cue_buttons) > 0:
            for button in self.plan_cue_buttons:
                button.destroy()
        self.plan_cue_buttons.clear()

        self._build_plan_cue_buttons()

    def reload(self):
        if self.startup.contains_qlxd:
            self.qlxd.stop = True
            for init in self.qlxd.qlxd_class_inits:
                logger.debug('stopping async event loop for qlxd init %s', init.IP_ADDR)
                init.loop.stop()

        if self.startup.contains_qlxd:
            self.qlxd.stop = True
        self.plan_window.destroy()
        self.kipro_ui.kill_threads()

        reloaded_ui = MainUI(startup=self.startup)
        reloaded_ui.build_plan_window()

    def convert_service_items_app_cues_to_dict_and_validate(self, service_items: List[Dict]) -> List[Dict]:
        """
        If service items in the self.service_items contain app cues, convert app cues from json to python dict.
        If there is something wrong with the data in them, do not use them & update them on PCO
        :param service_items retrieved from the pco_plan.get_service_items method
        :return: new service items with app cues converted from json to a python dict
        """

        logger.debug(f'{__class__.__name__}.{self.convert_service_items_app_cues_to_dict_and_validate.__name__}')

        for item in service_items:
            if 'App Cues' in item['notes']:

                app_cues_from_plan: str = item['notes']['App Cues']
                validated_cues = self.pco_plan.validate_plan_item_app_cues(app_cues_from_plan) # this will be the same string if valid, None if invalid

                # Check for PVP cues created before May 30, 2024 and fix them:
                has_been_modified: bool = False
                if validated_cues is not None:
                    validated_cues = json.loads(validated_cues)
                    for cue in validated_cues['action_cues']:
                        device = self.cue_handler.get_device_from_uuid(cue['uuid'])
                        if device['type'] == 'pvp':
                            if 'cue_name' in cue.keys():
                                has_been_modified = True
                                cue.pop('cue_name')
                                cue['cue_type'] = 'cue_cue'
                                logger.info(f'{__class__.__name__}.{self.convert_service_items_app_cues_to_dict_and_validate.__name__}: Found PVP cues of old format, updating...')

                    validated_cues = json.dumps(validated_cues)
                    item['notes']['App Cues'] = validated_cues

                    if has_been_modified:
                        self.pco_plan.create_and_update_item_app_cue(item_id=item['id'], app_cue=validated_cues)

                # if cues are invalid, remove from pco and from the python dict, else deserialize them and put them back into the dict to be returned
                if validated_cues is None:
                    logger.warning(f'{__class__.__name__}.{self.convert_service_items_app_cues_to_dict_and_validate.__name__}: Invalid cues found, removing them.')
                    self.pco_plan.remove_item_app_cue(item['id'])
                    item['notes'].pop('App Cues')
                else:
                    item['notes']['App Cues'] = json.loads(item['notes']['App Cues'])

        return service_items

    @staticmethod
    def convert_plan_app_cues_to_dict(plan_app_cues: str) -> List[Dict]:
        """
        Convert the string version of app cues stored in PCO's plan note section to a python dict
        :param plan_app_cues: the string version of app cues stored in PCO's plan note section
        :return: python dict of app cues
        """

        return json.loads(plan_app_cues)

    def check_if_current_added_cues_and_devices_valid_and_online(self) -> None:
        """
        Check if a device is offline, or there are any old or invalid cues on an item, for example,
         if there's a cue to play a PVP video, but that cue no longer exists on the pvp machine.
        If a cue is invalid, create a warning button on the plan item that opens the cue creator for that item
        :return:
        """

        logger.debug('Checking if cues are valid and devices are online')

        # this list contains a bool for each plan item.
        # If the item contains a cue that has an error, bool is set to True below.
        item_is_errored: List[bool] = []

        for i, plan_item in enumerate(self.plan_items):
            item_is_errored.append(False)
            if 'App Cues' in plan_item['notes']:
                action_cues = plan_item['notes']['App Cues']['action_cues']
                item_is_errored.append(False)
                is_valid = self.cue_handler.cues_are_valid(action_cues)
                for cue in is_valid:
                    if False in cue.keys():
                        item_is_errored[i] = True

        for item, frame, is_errored in zip(self.plan_items, self.item_frames, item_is_errored):
            if not item['type'] == 'header' and is_errored:
                Button(frame, image=self.cue_warning_icon, anchor='w', bg=bg_color, command=lambda item=item:
                       CueCreator(startup=self.startup, ui=self, devices=self.startup.devices).create_plan_item_cue(input_item=item)
                    ).pack(side=RIGHT, padx=30)


    def _build_current_service_time(self):
        logger.debug('Building current service time info')
        current_service_time = self.pco_plan.get_current_live_service()
        if not current_service_time is None:
            logger.debug('Live service info: %s', current_service_time)
            self.current_service_frame.grid(row=0, column=0, sticky='w')
            Label(self.current_service_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Current Live Service:  ').grid(row=0, column=0)
            Label(self.current_service_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=current_service_time['local']).grid(row=0, column=1)

    def _build_clock(self):
        """
        Builds main clock at the top of the window.
        Also checks for advance to next cues.
        :return:
        """
        time_label = Label(self.clock_frame,
                           fg=clock_text_color,
                           bg=bg_color,
                           font=(clock_text_font, clock_text_size))
        self.clock_frame.grid(row=1, column=0, sticky='w')
        time_label.grid(row=0, column=0, padx=10)

        auto_advance_time_remaining_label = Label(self.clock_frame, fg=accent_color_1, bg=bg_color, font=(clock_text_font, 10), text='')
        auto_advance_time_remaining_label.grid(row=1, column=0, sticky='W', padx=10)


        # udpates clock and checks for advance to next cues
        def tick():
            time_string = time.strftime('%H:%M:%S')
            time_label.config(text=time_string)
            time_label.after(1000, tick)

            current_item_notes = self.plan_items[self.current_item_index-1]['notes'] # notes in the current item

            if 'App Cues' in current_item_notes:
                # advance to next on time
                if len(current_item_notes['App Cues']['advance_to_next_on_time']) > 0: # if there's an advance to next on time cue in the current item

                    current_time = dt.datetime.now().time()
                    current_time_in_seconds = (current_time.hour * 3600) + (current_time.minute * 60) + current_time.second

                    def cue_time_to_seconds(cue_time_list: list) -> int: # convert the [01, 02, 03] list format to seconds value
                        return (int(cue_time_list[0]) * 3600) + (int(cue_time_list[1]) * 60) + (int(cue_time_list[2]))

                    def find_difference(cue_time): # difference in time between cue time and now
                        return cue_time_to_seconds(cue_time)-current_time_in_seconds

                    soonest_advance_time_index = 0
                    for iteration, cue_time in enumerate(current_item_notes['App Cues']['advance_to_next_on_time'], start=0):
                        difference = find_difference(cue_time)  # difference in time between now and advance time
                        if difference < 0:  # pass if the cue time is in the past
                            pass
                        else:
                            current_smallest_time = find_difference(current_item_notes['App Cues']['advance_to_next_on_time'][soonest_advance_time_index])
                            if current_smallest_time < 0:
                                soonest_advance_time_index = iteration
                            else:
                                if difference < current_smallest_time:
                                        soonest_advance_time_index = iteration

                    countdown = find_difference(current_item_notes['App Cues']['advance_to_next_on_time'][soonest_advance_time_index])

                    # auto advance delay
                    if self.advance_to_next_schedule_has_been_delayed:
                        countdown += self.advance_to_next_delay

                    auto_advance_time_remaining_label.configure(text=f'Advancing to next item in {time.strftime("%H:%M:%S", time.gmtime(countdown))}')


                    if countdown == 0 and not self.auto_advance_on_time_cancelled_by_user:  # advance to next
                        logger.info(f'Auto advancing to next on time')
                        self.next(cue_items=True)
                    if countdown == 0:
                        self.auto_advance_on_time_cancelled_by_user = False
                        self.auto_advance_reminder_frame.place_forget()
                    elif countdown in list(range(30)) and not self.auto_advance_on_time_cancelled_by_user:  # show advance to next message
                        self.auto_advance_reminder_label.configure(text=f'Advancing to next item in {countdown} seconds')
                        self.auto_advance_reminder_frame.place(relx=.5, rely=.45, anchor=CENTER)

                # advance to next automatically after the current item finishes
                if current_item_notes['App Cues']['advance_to_next_automatically'] is True:

                    # small auto advance label if it hasn't been cancelled
                    if not self.auto_advance_on_time_cancelled_by_user and self.current_item_timer_input >= 0:
                        auto_advance_time_remaining_label.configure(text=f'Advancing to next item in {time.strftime("%H:%M:%S", time.gmtime(self.current_item_timer_input))}')
                    else:
                        # user clicked cancel, "remove" the label
                        auto_advance_time_remaining_label.configure(text='')

                    # if current item timer is greater than 0 and less than 30, time remaining is positive, and has not been cancelled
                    if 0 < self.current_item_timer_input <= 30 and self.time_remaining_is_positive and not self.auto_advance_automatically_cancelled_by_user:
                        self.auto_advance_reminder_label.configure(text=f'Advancing to next item in {self.current_item_timer_input} seconds')
                        self.auto_advance_reminder_frame.place(relx=.5, rely=.3, anchor=CENTER)
                    if self.current_item_timer_input == 0 and not self.auto_advance_on_time_cancelled_by_user:
                        logger.debug('auto advancing to next automatically because current item timer has ended')
                        self.next(cue_items=True)
                        self.auto_advance_reminder_frame.place_forget()
                    if self.current_item_timer_input == 0:
                        self.auto_advance_automatically_cancelled_by_user = False
                        self.auto_advance_reminder_frame.place_forget()
            else:
                self.auto_advance_reminder_frame.place_forget()
                auto_advance_time_remaining_label.configure(text='')


        tick()

    def _build_auto_advance_reminder_ui(self):
        self.auto_advance_reminder_frame = Frame(self.plan_window, bg=accent_color_1)
        self.auto_advance_reminder_label = Label(self.auto_advance_reminder_frame, fg=reminder_color, bg=accent_color_1, font=(font, reminder_font_size))
        self.auto_advance_reminder_label.grid(row=0, column=0)

        def cancel():
            logger.debug('cancelling auto advance to next')
            self.auto_advance_on_time_cancelled_by_user = True
            self.auto_advance_automatically_cancelled_by_user = True
            self.auto_advance_reminder_frame.place_forget()

        Button(self.auto_advance_reminder_frame, bg=accent_color_1, fg=reminder_color, font=(font, reminder_font_size), text='CANCEL', command=cancel).grid(row=0, column=1)

    # Countdown timer for items. Receives time from class variable self.current_item_timer_input
    def _build_item_timer(self):
        time_label = Label(self.clock_frame,
                           fg=clock_text_color,
                           bg=bg_color,
                           font=(clock_text_font, clock_text_size))
        time_label.grid(row=0, column=1, padx=10)

        def tick():
            if self.current_item_timer_input == 0:
                self.time_remaining_is_positive = False

            if not self.time_remaining_is_positive:
                self.current_item_timer_input += 1
                time_label.configure(fg=clock_overrun_color)
            else: # color green
                self.current_item_timer_input -= 1
                time_label.configure(fg='#317c42')

            time_string = time.strftime('%M:%S', time.gmtime(self.current_item_timer_input))
            time_label.configure(text=time_string)

            self.clock_frame.after(1000, tick)
        tick()

    def _build_global_cues_button(self):
        def open_global_cues_window() -> None:
            GlobalCues().open_global_cues_window()
        Button(self.clock_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
               text='Global Cues', command=open_global_cues_window).grid(row=0, column=4, padx=10)

    def _build_items_view(self):

        # Item frames
        for item in self.plan_items:
            # Add item frames to list
            if item['type'] == 'header':
                item_frame_height = 25
                item_frame_color = header_color
            else:
                item_frame_height = 28
                item_frame_color = bg_color
            item_frame = Frame(self.service_plan_frame, bg=item_frame_color, width=plan_item_frame_width, height=item_frame_height)
            self.item_frames.append(item_frame)

        # separators
        for frame in self.item_frames:
            separator = Frame(self.service_plan_frame, bg=separator_color, width=plan_item_frame_width, height=1)
            separator.pack_propagate(False)
            separator.pack()

            frame.pack_propagate(0)
            frame.pack()

            self.separators.append(separator)

        # Item times
        for item, frame in zip(self.plan_items, self.item_frames):
            if not item['type'] == 'header':
                time_str = time.strftime('%M:%S', time.gmtime(item['length']))
                label = Label(frame, bg=bg_color, fg=text_color, font=(font, item_time_size), text=time_str)
                self.item_time_labels.append(label)
                label.pack(side=LEFT)
            else:
                self.item_time_labels.append(None)

        # Spacer between item times and item titles
        for item, frame in zip(self.plan_items, self.item_frames):
            if not item['type'] == 'header':
                label = Label(frame, bg=bg_color, font=(font, item_time_size), text='')
                self.item_spacer_labels.append(label)
                label.pack(side=LEFT)
            else:
                self.item_spacer_labels.append(None)

        # Item titles
        for item, frame in zip(self.plan_items, self.item_frames):
            if item['type'] == 'header':
                bg = header_color
                title_size = header_font_size
            else:
                bg = bg_color
                title_size = plan_text_size

            if item['type'] == 'song':
                fg = song_title_color
            else:
                fg = text_color

            label = Label(frame, bg=bg, fg=fg, text=item['title'], font=(font, title_size))
            self.item_title_labels.append(label)
            label.pack(side=LEFT)

        # Item people
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'Person' in item['notes']:
                label = Label(frame, bg=bg_color, fg=text_color, text=item['notes']['Person'], font=(font, plan_text_size-2))
                self.item_person_labels.append(label)
                label.place(anchor='nw', x=400)
            else:
                self.item_person_labels.append(None)

        # Item producer notes
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'Producer Notes' in item['notes']:
                label = Label(frame, bg=bg_color, fg=text_color, text=item['notes']['Producer Notes'], font=(font, producer_note_text_size))
                self.item_producer_note_labels.append(label)
                label.place(anchor='nw', x=700)
            else:
                self.item_producer_note_labels.append(None)

        # Item app cues
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'App Cues' in item['notes']:
                label_text = ''
                for cue in self.cue_handler.verbose_decode_cues(cuelist=item['notes']['App Cues']['action_cues']):
                    label_text = f'{label_text}{cue}\n'
                label = Label(frame, bg=bg_color, fg=text_color, text=label_text, justify=LEFT,
                      font=(font, app_cue_font_size))
                self.item_app_cue_labels.append(label)
                label.place(anchor='nw', x=1050)

                # if number of cues on an item is greater than 4, increase height of item frame so nothing is cut off
                number_of_cues = len(self.cue_handler.verbose_decode_cues(cuelist=item['notes']['App Cues']['action_cues']))
                if number_of_cues > 2:
                    over = number_of_cues - 2
                    height = 28 + (10 * over)
                    frame.configure(height=height)
            else:
                self.item_app_cue_labels.append(None)

        # Item auto advance labels
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'App Cues' in item['notes'] and len(item['notes']['App Cues']['advance_to_next_on_time']) > 0: # advance to next on time cues exist in current item
                advance_cue_times = []
                for advance_time in item['notes']['App Cues']['advance_to_next_on_time']:
                    advance_cue_times.append(advance_time)

                    #create label with no text
                    auto_advance_label = Label(frame, bg=bg_color, fg=text_color, font=(font, app_cue_font_size + 1),
                                               justify=LEFT)
                    auto_advance_label.place(anchor='nw', x=900)

                if len(advance_cue_times) == 0:
                    self.item_advance_cue_labels.append(None)
                else:
                    self.item_advance_cue_labels.append(auto_advance_label)

                # add text to label
                advance_time_text = ''
                for iteration, advance_time in enumerate(advance_cue_times):
                    advance_time_text += f'ADVANCE TO NEXT AT {advance_time[0]}:{advance_time[1]}:{advance_time[2]}'
                    if not iteration + 1 == len(advance_cue_times):
                        advance_time_text += '\n'
                    auto_advance_label.configure(text=advance_time_text)
            else:
                self.item_advance_cue_labels.append(None)

        # Item auto advance to next arrow
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'App Cues' in item['notes'] and item['notes']['App Cues']['advance_to_next_automatically']:
                logger.debug('Placing advance to next arrow on item %s', item['title'])
                advance_label = Label(frame, bg=bg_color, fg=text_color, justify=LEFT, image=self.auto_advance_arrow_image)
                advance_label.place(anchor='nw', x=1345)
                self.item_advance_to_next_automatically_arrow_images.append(advance_label)
            else:
                self.item_advance_to_next_automatically_arrow_images.append(None)

        # Item 'options' button
        for item, frame in zip(self.plan_items, self.item_frames):
            if not item['type'] == 'header':
                Button(frame, image=self.gear_icon, anchor='w', font=(font, options_button_text_size),
                       bg=bg_color, fg=text_color, command=lambda item=item:
                    CueCreator(startup=self.startup, ui=self, devices=self.startup.devices).create_plan_item_cue(input_item=item)
                    ).pack(side=RIGHT)

    def _build_kipro_status(self):
        self.kipro_control_frame.grid(row=4, column=2, sticky='n')

        # Buttons
        for kipro_unit in self.all_kipros:
            button = Button(self.kipro_control_frame, text=kipro_unit['user_name'], font=(font, other_text_size), fg=text_color, height=2, width=11, relief=FLAT,
                            command=lambda kipro_unit=kipro_unit: (self.kipro.toggle_start_stop(ip=kipro_unit['ip_address'], name=kipro_unit['user_name']), self.kipro_ui.update_kipro_status(ui=self)))
            self.kipro_buttons.append(button)

        # Storage remaining bars
        for kipro_unit in self.all_kipros:
            progress = ttk.Progressbar(self.kipro_control_frame, length=110, mode='determinate', maximum=100)
            self.kipro_storage_remaining_bars.append(progress)

        for button, progress in zip(self.kipro_buttons, self.kipro_storage_remaining_bars):
            button.pack()
            progress.pack()

        self.kipro_ui.update_kipro_status(ui=self)

    def _build_qlxd_ui(self):
        self.qlxd = ShureQLXDUi(devices=self.startup.devices, ui=self, inits=self.startup.qlxd_class_inits)
        self.qlxd_frame.grid(row=7, column=0, sticky='e')
        self.qlxd_frame.configure(height=60, width=plan_item_frame_width)

        self.qlxd.main_loop()

    def _build_plan_cue_buttons(self):
        """
        Build plan cues at the bottom of the screen above previous/next. Data is acquired from the
        plan notes section on PCO.

        Will also check to see if the cues on each plan cue are valid. Colors the button accordingly if not.
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self._build_plan_cue_buttons.__name__}')

        if self.pco_plan.check_if_plan_app_cue_exists():
            plan_app_cues: str = self.pco_plan.get_plan_app_cues()
            plan_app_cues_validated = self.pco_plan.validate_plan_cues(plan_app_cues)

            # pco_plan.validate_plan_cues can return none if invalid data is found
            if plan_app_cues_validated is not None:
                self.plan_cues_frame.grid(row=5, column=0)

                self.plan_cues = self.convert_plan_app_cues_to_dict(plan_app_cues_validated)

                for iteration, cue in enumerate(self.plan_cues):
                    cue_name = cue[0]
                    cue_data = cue[1]
                    button = Button(self.plan_cues_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                           text=cue_name, command=lambda cue_data=cue_data: threading.Thread(target=self.cue_handler.activate_cues(cue_data['action_cues'])).start())
                    button.grid(row=0, column=iteration, padx=plan_cue_pad_x, pady=10)
                    self.plan_cue_buttons.append(button)

                #fix old pvp cues as of may 30, 2024. This must be done outside of the below loop
                to_upload_new_plan_cues: list = [False]
                for i, plan_cue in enumerate(self.plan_cues):
                    has_been_modified: list = [False]
                    plan_cue_actions = plan_cue[1]['action_cues']
                    for cue in plan_cue_actions:
                        device = self.cue_handler.get_device_from_uuid(cue['uuid'])
                        if device['type'] == 'pvp':
                            if 'cue_name' in cue.keys():
                                to_upload_new_plan_cues[0] = True
                                has_been_modified[0] = True
                                cue.pop('cue_name')
                                cue['cue_type'] = 'cue_cue'
                                logger.info(f'{__class__.__name__}.{self._build_plan_cue_buttons.__name__}: Plan cue with old PVP cue found. Fixing...')
                        if has_been_modified[0]:
                            self.plan_cues[i][1]['action_cues'] = plan_cue_actions
                if to_upload_new_plan_cues[0]:
                    self.pco_plan.create_and_update_plan_app_cues(json.dumps(self.plan_cues))

                # Check if cues on plan cues are valid. Color accordingly if not
                for plan_cue, button in zip(self.plan_cues, self.plan_cue_buttons):
                    plan_cue_actions = plan_cue[1]['action_cues']
                    is_valid = True
                    valid_check = self.cue_handler.cues_are_valid(plan_cue_actions)
                    for cue in valid_check:
                        if False in cue.keys():
                            is_valid = False
                    if not is_valid:
                        logger.info(f'Found invalid cues on plan cue {plan_cue[0]}')
                        button.configure(bg='#ffc639', fg=accent_text_color)

            else:
                logger.info(f'{__class__.__name__}.{self._build_plan_cue_buttons.__name__}: Plan app cues were invalid, skipping adding buttons.')
        else:
            logger.debug(f'{__class__.__name__}.{self._build_plan_cue_buttons.__name__}: No plan cues being added because none were found.')

    def _build_aux_control(self):
        """
        Builds buttons for next/previous
        :return: None.
        """
        self.aux_controls_frame.grid(row=6, column=0)
        self.aux_controls_frame.configure(height=60, width=plan_item_frame_width)

        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Previous (no actions)', font=(accent_text_font, 10), command=lambda: self.previous(cue_items=False)).grid(row=1, column=1, padx=next_previous_pad_x)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Previous', font=(accent_text_font, accent_text_size), command=lambda: self.previous(cue_items=True)).grid(row=1, column=2, padx=next_previous_pad_x)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Next', font=(accent_text_font, accent_text_size), command=lambda: self.next(cue_items=True)).grid(row=1, column=3, padx=next_previous_pad_x)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Next (no actions)', font=(accent_text_font, 10), command=lambda: self.next(cue_items=False)).grid(row=1, column=4, padx=next_previous_pad_x)

    # mousewheel event handler
    def _on_mousewheel(self, event):
        self.plan_items_canvas.yview_scroll(math.floor(-1*(int(event.delta))/120), 'units')

    # Creates plan frame height, scrollbar, binds mousewheel & scrollbar, set current item timer to current live item
    def _ui_cleanup(self):
        self.service_plan_frame_height = 0 if self.service_plan_frame_height is None else self.service_plan_frame_height

        # used if refreshing app. Set to 0 if height is greater than 0, otherwise height will be added onto current height
        if self.service_plan_frame_height != 0:
            self.service_plan_frame_height = 0

        for frame in self.item_frames:  # find height of all item frames together, used to pass to the plan frame before creation of the scrollbar
            frame.update()
            height = frame.winfo_height()
            self.service_plan_frame_height += height
        logger.debug('service_plan_frame height is %s', self.service_plan_frame_height)

        self.service_plan_frame.configure(height=self.service_plan_frame_height+50)
        self.items_view_scrollbar = Scrollbar(self.plan_window, command=self.plan_items_canvas.yview)
        self.plan_items_canvas.configure(scrollregion=self.plan_items_canvas.bbox('all'), yscrollcommand=self.items_view_scrollbar.set)
        self.items_view_scrollbar.grid(row=4, column=1, sticky='nsw')

        self.service_plan_frame.bind_all('<MouseWheel>', self._on_mousewheel)

        # set current item timer to live item, for use when plan is first loaded
        logger.debug('Updating current item timer upon ui startup with time %s', self.plan_items[self.current_item_index]['length'])
        self.update_item_timer(self.plan_items[self.current_item_index - 1]['length'])

    def _cue(self, is_next: bool=True):
        """
        Called when next or previous functions are called. it will cue actions on the next item when next=True,
        cues actions on previous items when next=False

        :param is_next: bool of whether to cue actions on the next or the previous cue
        :return: NOon
        """

        logger.debug(f'{__class__.__name__}.{self._cue.__name__}: Cueing cues on plan item.')
        def activate(cuelist: list) -> None:
            """
            Activates cuelist in a new thread. If Sound Check Mode is active, ignore cues on specified device(s).
            :param cuelist: list of cues to activate.
            :return: None.
            """
            ignored_devices = SoundCheckModeOptions.read_sound_check_mode_devices()

            cuelist_minus_ignored = []

            for cue in cuelist:
                if cue['uuid'] not in ignored_devices:
                    cuelist_minus_ignored.append(cue)

            if self.sound_check_mode:
                logger.info(f'{__class__.__name__}.{self._cue.__name__}: Sound check mode is active. Ignoring cues from {len(ignored_devices)} devices.')
                threading.Thread(target=lambda: self.cue_handler.activate_cues(cuelist=cuelist_minus_ignored)).start()
            else:
                threading.Thread(target=lambda: self.cue_handler.activate_cues(cuelist=cuelist)).start()


        if is_next:
            if 'App Cues' in self.plan_items[self.next_item_index]['notes']:
                activate(self.plan_items[self.next_item_index]['notes']['App Cues']['action_cues'])

                # set reminder
                for cue in self.plan_items[self.next_item_index]['notes']['App Cues']['action_cues']:
                    if cue['uuid'] == 'b652b57e-c426-4f83-87f3-a7c4026ec1f0':
                        time = (int(cue['minutes']) * 60) + int(cue['seconds'])
                        self._set_reminder(reminder_time=time, reminder_text=cue['reminder'])
        if not is_next:
            if 'App Cues' in self.plan_items[self.previous_item_index]['notes']:

                activate(self.plan_items[self.previous_item_index]['notes']['App Cues']['action_cues'])

                # set reminder
                for cue in self.plan_items[self.previous_item_index]['notes']['App Cues']['action_cues']:
                    if cue['uuid'] == 'b652b57e-c426-4f83-87f3-a7c4026ec1f0':
                        time = (int(cue['minutes']) * 60) + int(cue['seconds'])
                        self._set_reminder(reminder_time=time, reminder_text=cue['reminder'])

    # Schedule a reminder. Reminder_time in seconds.
    def _set_reminder(self, reminder_time: int, reminder_text: str) -> None:
        reminder_frame = Frame(self.plan_window, bg=accent_color_1)

        Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text=reminder_text, font=(font, reminder_font_size)).grid(row=0, column=1)
        Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text='REMINDER:  ',font=(accent_text_font, accent_text_size)).grid(row=0, column=0)
        Button(reminder_frame, fg=reminder_color, bg=accent_color_1, text='clear', font=(accent_text_font, accent_text_size), command=reminder_frame.destroy).grid(row=0, column=2)

        def show_reminder():
            logger.debug('Showing reminder %s', reminder_text)
            reminder_frame.place(relx=.5, rely=.5, anchor=CENTER)

        reminder_frame.after(reminder_time*1000, show_reminder)


class KiProUi:
    def __init__(self):
        self.kipro = KiPro()
        self.exit_event = threading.Event()

    def kill_threads(self):
        logger.debug(f'{__class__.__name__}.{self.kill_threads.__name__}: Setting exit event')
        self.exit_event.set()

    def update_kipro_status(self, ui):
        for iteration, kipro_unit in enumerate(ui.all_kipros):

            status = int(self.kipro.get_status(ip=kipro_unit['ip_address']))
            # logger.debug('update_kipro_status: status is %s for kipro %s', status, kipro_unit['name'])
            ui.update_kipro_status(kipro_unit=iteration, status=status)

            percent = int(self.kipro.get_remaining_storage(ip=kipro_unit['ip_address']))
            # logger.debug('update_kipro_status: storage is %s percent for kipro %s', percent, kipro_unit['name'])
            ui.update_kipro_storage(kipro_unit=iteration, percent=percent)

        if interval_update_kipros:
            threading.Thread(name='kipro_refresh', target=lambda: self._refresh(interval=kipro_update_interval, ui=ui)).start()

    def _refresh(self, interval, ui):
        # logger.debug(f'KiProUi.__refresh: exit_event.is_set(): {self.exit_event.is_set()}')

        time.sleep(interval)
        if not self.exit_event.is_set():
            self.update_kipro_status(ui=ui)
        else:
            logger.debug('KiProUi.__refresh: exit event set, stopping loop')


class ShureQLXDUi:
    def __init__(self, devices, ui, inits):
        self.devices = devices
        self.main_ui = ui

        self.stop = False

        self.qlxd_class_inits = inits
        self.qlxd_device_names = []

        self.qlxd_channel_boxes = []
        self.qlxd_box_names = []
        self.qlxd_box_rf_labels = []
        self.qlxd_box_rf_levels = []
        self.qlxd_box_audio_labels = []
        self.qlxd_box_audio_levels = []
        self.qlxd_box_battery_levels = []
        self.battery_icon_canvases = []

        for init in self.qlxd_class_inits:
            for name in init.channel_names:
                self.qlxd_device_names.append(name)

        self.box_problem_color = live_color

        subsample_x = 16
        subsample_y = 16

        self.battery_level_off_image = PhotoImage(file=os.path.join(abs_path, 'battery_level_off.png')).subsample(subsample_x, subsample_y)
        self.battery_level_0_image = PhotoImage(file=os.path.join(abs_path, 'battery_level_0.png')).subsample(subsample_x, subsample_y)
        self.battery_level_1_image = PhotoImage(file=os.path.join(abs_path, 'battery_level_1.png')).subsample(subsample_x, subsample_y)
        self.battery_level_2_image = PhotoImage(file=os.path.join(abs_path, 'battery_level_2.png')).subsample(subsample_x, subsample_y)
        self.battery_level_3_image = PhotoImage(file=os.path.join(abs_path, 'battery_level_3.png')).subsample(subsample_x, subsample_y)
        self.battery_level_4_image = PhotoImage(file=os.path.join(abs_path, 'battery_level_4.png')).subsample(subsample_x, subsample_y)
        self.battery_level_5_image = PhotoImage(file=os.path.join(abs_path, 'battery_level_5.png')).subsample(subsample_x, subsample_y)

        self.battery_images = [self.battery_level_off_image, self.battery_level_0_image, self.battery_level_1_image,
                               self.battery_level_2_image, self.battery_level_3_image, self.battery_level_4_image,
                               self.battery_level_5_image]

        self._create_channel_boxes()


    def _create_channel_boxes(self):
        for _ in self.qlxd_device_names:
            f = Frame(self.main_ui.qlxd_frame, bg=bg_color, width=100, height=50)
            f.pack_propagate(0)
            f.pack(side=LEFT, padx=5, pady=10)
            self.qlxd_channel_boxes.append(f)

        for box, channel_info in zip(self.qlxd_channel_boxes, self.qlxd_device_names):  # Channel name labels
            name = Label(box, bg=bg_color, fg=text_color, text=channel_info, font=(font, 9))
            self.qlxd_box_names.append(name)
            name.place(x=0, y=0)

        # channel RF labels
        for box in self.qlxd_channel_boxes:
            r = Label(box, bg=bg_color, fg=text_color, text='RF:', font=(font, 6))
            self.qlxd_box_rf_labels.append(r)
            r.place(x=0, y=20)

        # channel RF strength
        for box in self.qlxd_channel_boxes:
            r = Label(box, bg=bg_color, fg='#ffffff', text='', font=(font, 3))
            self.qlxd_box_rf_levels.append(r)
            r.place(x=24, y=23)

        # channel audio labels
        for box in self.qlxd_channel_boxes:
            r = Label(box, bg=bg_color, fg=text_color, text='AUD:', font=(font, 6))
            self.qlxd_box_audio_labels.append(r)
            r.place(x=0, y=33)

        # channel audio strength
        for box in self.qlxd_channel_boxes:
            r = Label(box, bg=bg_color, fg='#ffffff', text='', font=(font, 3))
            self.qlxd_box_audio_levels.append(r)
            r.place(x=24, y=36)

        # battery level images
        for box in self.qlxd_channel_boxes:
            b = Label(box, image=self.battery_images[0], bg=bg_color)
            self.qlxd_box_battery_levels.append(b)
            b.place(x=63, y=0)

    def _stop_all_metering(self):
        for init in self.qlxd_class_inits:
            init.stop_all_metering()

    def _update_battery_ui(self, levels):
        for level, box_image in zip(levels, self.qlxd_box_battery_levels):
            try:
                box_image.configure(image=self.battery_images[level['bat']+1])
            except IndexError:
                box_image.configure(image=self.battery_images[0])

    def main_loop(self):
        # self.__stop_all_metering()
        logger.debug('ShureQLXDUi.main_loop: Starting')
        total_characters_in_progress_bar = 36
        self.stop = False

        for init in self.qlxd_class_inits:  # set event loop for each qlxd unit
            init.set_event_loop()

        def single_unit_loop(init, channel_boxes, box_names, box_rf_labels, box_rf_levels, box_audio_levels, box_audio_labels, box_battery_levels):
            def run():
                for device_level in init.continuous_meter():
                    if not self.stop:
                        for level, channel_box, box_name, box_rf_label, box_rf_level, box_audio_level, box_audio_label, box_battery_level in zip(device_level, channel_boxes, box_names, box_rf_labels, box_rf_levels, box_audio_levels, box_audio_labels, box_battery_levels):
                            try:
                                characters_in_rf = round(int(level['rf']) * (total_characters_in_progress_bar / 115))
                                characters_in_aud = round(int(level['aud']) * (total_characters_in_progress_bar / 50))

                                rf_str = ''
                                for _ in range(characters_in_rf):
                                    rf_str += '#'
                                box_rf_level.configure(text=rf_str)

                                aud_str = ''
                                for _ in range(characters_in_aud):
                                    aud_str += '#'
                                box_audio_level.configure(text=aud_str)

                            except TypeError:
                                pass

                            try:
                                box_battery_level.configure(image=self.battery_images[int(level['bat']) + 1])
                            except IndexError:
                                box_battery_level.configure(image=self.battery_images[0])

                            try:
                                if int(level['rf']) < 40 or level['bat'] == 255:
                                    channel_box.configure(bg=live_color)
                                    box_name.configure(bg=live_color)
                                    box_rf_label.configure(bg=live_color)
                                    box_rf_level.configure(bg=live_color)
                                    box_audio_level.configure(bg=live_color)
                                    box_audio_label.configure(bg=live_color)
                                    box_battery_level.configure(bg=live_color)

                                elif int(level['rf']) > 40 and int(level['bat']) <= 2:
                                    channel_box.configure(bg='#bf7831')
                                    box_name.configure(bg='#bf7831')
                                    box_rf_label.configure(bg='#bf7831')
                                    box_rf_level.configure(bg='#bf7831')
                                    box_audio_level.configure(bg='#bf7831')
                                    box_audio_label.configure(bg='#bf7831')
                                    box_battery_level.configure(bg='#bf7831')

                                else:
                                    channel_box.configure(bg=kipro_idle_color)
                                    box_name.configure(bg=kipro_idle_color)
                                    box_rf_label.configure(bg=kipro_idle_color)
                                    box_rf_level.configure(bg=kipro_idle_color)
                                    box_audio_level.configure(bg=kipro_idle_color)
                                    box_audio_label.configure(bg=kipro_idle_color)
                                    box_battery_level.configure(bg=kipro_idle_color)
                            except Exception as e:
                                logger.debug('tk error for qlxd init %s, exception: %s', init.IP_ADDR, e)
                                pass
                    else:
                        logger.debug('ShureQLXDUi.main_loop.single_unit_loop for ip %s: self.stop = True', init.IP_ADDR)
                        break

            try:
                run()
            except RuntimeError:
                logger.debug('Broke async event loop for qlxd %s', init.IP_ADDR)
                run()
            except _tkinter.TclError as e: # plan was reloaded
                logger.debug('qlxdui tk error: %s', e)
                run()

        for iteration, init in enumerate(self.qlxd_class_inits, start=1):
            start_index = iteration*4-4
            end_index = iteration*4
            t = threading.Thread(target=lambda: single_unit_loop(
                init=init,
                channel_boxes=self.qlxd_channel_boxes[start_index:end_index],
                box_names=self.qlxd_box_names[start_index:end_index],
                box_rf_labels=self.qlxd_box_rf_labels[start_index:end_index],
                box_rf_levels=self.qlxd_box_rf_levels[start_index:end_index],
                box_audio_labels=self.qlxd_box_audio_labels[start_index:end_index],
                box_audio_levels=self.qlxd_box_audio_levels[start_index:end_index],
                box_battery_levels=self.qlxd_box_battery_levels[start_index:end_index]
            ))

            t.name = f'ShureQLXDUI_{init.IP_ADDR}'
            t.start()

            logger.debug(f'{__class__.__name__}.{self.main_loop.__name__}: Thread name for ULXD/QLXD unit ui thread under'
                         f'ShureQLXDUi.main_loop {init.IP_ADDR} is {t.name}')


class Main:   # startup
    def __init__(self):
        os.chdir(abs_path)

        if os.path.exists(os.path.join('configs', 'devices.json')):
            with open(os.path.join('configs', 'devices.json'), 'r') as f:
                self.devices = json.loads(f.read())
        else:
            logger.warning('Did not find devices.json file')
            DeviceEditor().build_default_file()
            with open(os.path.join('configs', 'devices.json'), 'r') as f:
                self.devices = json.loads(f.read())

        if os.path.exists(os.path.join('configs', 'persistent_plan_data.json')):
            with open(os.path.join('configs', 'persistent_plan_data.json')) as f:
                self.persistent_plan_data = json.loads(f.read())



        # qlxd initialization only happens once. Use this var to keep track of if the "main" method has been run or not.
        self.has_started = False

        self.contains_qlxd = False
        for device in self.devices:
            if device['type'] == 'shure_qlxd':
                self.contains_qlxd = True
                break

        if self.contains_qlxd and not self.has_started:
            self.qlxd_class_inits = []
            for device in self.devices:
                if device['type'] == 'shure_qlxd':
                    self.qlxd_class_inits.append(ShureQLXD(ip=device['ip_address']))
            self.has_started = True

            for init in self.qlxd_class_inits:
                init.startup()

        self.main_service = SelectService()
        self.main_service.ask_service_info()

        self.service_type_id = self.main_service.service_type_id
        self.service_id = self.main_service.service_id

        del self.main_service

        # check to see if this specific plan has been opened or not. If it has been opened, delete all existing item cues so
        # it's opened fresh.
        self.persistent_plan_data = PersistentPlanData()
        has_been_opened = self.persistent_plan_data.has_plan_been_loaded(service_type_id=self.service_type_id, plan_id=self.service_id)

        if not has_been_opened:
            pco = PcoPlan(service_type=self.service_type_id, plan_id=self.service_id)
            pco.remove_all_item_app_cues()

        self.persistent_plan_data.add_plan_that_has_been_loaded(service_type_id=self.service_type_id, plan_id=self.service_id)

        CueHandler.check_and_update_plan_for_october_2022_cues(service_type_id=self.service_type_id,
                                                               service_id=self.service_id)

        self.main_ui = MainUI(startup=self)

        self.main_ui.build_plan_window()


if __name__ == '__main__':
    start = Main()