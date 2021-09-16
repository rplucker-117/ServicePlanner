try:
    from tkinter import *
    from tkinter import messagebox
    from settings import *
    import time
    from logzero import logger, logfile
    from pco_plan import PcoPlan
    from pco_live import PcoLive
    from tkinter import ttk
    import threading
    from cue_creator import CueCreator
    import logging
    import json
    import os
    from kipro import KiPro
    from rosstalk import rosstalk as rt
    import wget
    import pprint
    from sheet_reader import *
    from multiprocessing import Process, Lock
    import requests
    from flask_server import flask_server as fs
    import urllib.parse
    from device_editor import DeviceEditor
    from select_service import SelectService
    import datetime as dt
    import math
    from shure_qlxd_async import ShureQLXD
    import asyncio

except Exception as e:
    from setup import *
    import os
    print(e)
    os.system("Python main.py")


abs_path = os.path.dirname(__file__)

#logging: absolute paths
if not os.path.exists(os.path.join(abs_path, 'logs')):
    os.mkdir(os.path.join(abs_path, 'logs'))

log_file_name = os.path.join(os.path.join(abs_path, 'logs'),time.strftime('%Y_%m_%d__%H_%M') + '.log')
logfile(log_file_name)

logging.getLogger('urllib3').setLevel(logging.INFO)

class Utilities:
    def __init__(self, main_ui_window_init):
        self.main_ui_window = main_ui_window_init
        self.cue_handler = main_ui_window_init.cue_handler
        self.cue_handler_global = main_ui_window_init.cue_handler_global
        self.cue_handler_plan = main_ui_window_init.cue_handler_plan

        self.pco_live = PcoLive(service_type_id = self.main_ui_window.service_type_id, plan_id=self.main_ui_window.service_id)
        self.pco_plan = PcoPlan(service_type = self.main_ui_window.service_type_id, plan_id=self.main_ui_window.service_id)


        self.utilities_menu = Tk()

        self.kipro = KiPro()

    def open_utilities_menu(self):
        self.utilities_menu.geometry('400x400')
        self.utilities_menu.configure(bg=bg_color)

        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Start Live Service', font=(font, other_text_size), command=self.__start_live).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Advance to Next Service', font=(font, other_text_size), command=self.__advance_to_next_service).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Reload Plan', font=(font, other_text_size), command=self.__reload_plan).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Load Adjacent Plan', font=(font, other_text_size), command=self.__load_adjacent).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Format Kipros', font=(font, other_text_size), command=self.__format).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Download Kipro Clips', font=(font, other_text_size), command=self.__download).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Add Plan Cue', font=(font, other_text_size), command=self.__add_plan_cue).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Remove Plan Cue', font=(font, other_text_size), command=self.__remove_plan_cue).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Add Global Cue', font=(font, other_text_size), command=self.__add_global_cue).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Remove Global Cue', font=(font, other_text_size), command=self.__remove_global_cue).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Update switcher cam names from PCO positions', font=(font, other_text_size), command=self.__update_cam_names).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Open Device Editor', font=(font, other_text_size), command=self.__open_device_editor).pack()

        self.utilities_menu.mainloop()

    def __reload_plan(self):
        self.utilities_menu.destroy()
        self.main_ui_window.reload()

    def __open_device_editor(self):
        self.utilities_menu.destroy()
        DeviceEditor().build_ui()

    def __start_live(self):
        if self.pco_live.get_current_live_item() is None:
            self.pco_live.go_to_next_item()
            self.utilities_menu.destroy()
            self.main_ui_window.update_live(service_time=True)
        else:
            self.utilities_menu.destroy()

    def __advance_to_next_service(self):
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

    def __load_adjacent(self):
        self.utilities_menu.destroy()
        adjacent_plan = AdjacentPlanView(ui=self.main_ui_window)
        adjacent_plan.ask_adjacent_plan()

    def __format(self):
        yes_no = messagebox.askyesno('Format KiPros', message="Are you sure you want to format ALL KiPros?")
        if yes_no:
            for kipro_unit in self.main_ui_window.all_kipros:
                self.kipro.format_current_slot(ip=kipro_unit['ip_address'])

        self.utilities_menu.destroy()

    def __download(self):
        logger.debug('download kipro clips button pressed')
        self.utilities_menu.destroy()
        threading.Thread(target=self.kipro.download_clips).start()
        self.main_ui_window.kipro_ui.kill_threads()

    def __update_cam_names(self):
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

    def __add_plan_cue(self):
        self.utilities_menu.destroy()
        self.cue_handler_plan.create_cues()

    def __remove_plan_cue(self):
        logger.debug('Utilities.__remove_plan_cue clicked')
        self.utilities_menu.destroy()
        if self.pco_plan.check_if_plan_app_cue_exists():
            current_cues = self.pco_plan.get_plan_app_cues()

            remove_plan_cue_window = Tk()
            remove_plan_cue_window.configure(bg=bg_color)
            listbox = Listbox(remove_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size))
            listbox.pack()

            for iteration, item in enumerate(current_cues):
                name = item[0]
                listbox.insert(iteration, name)

            def okay():
                logger.debug('Utilities.__remove_plan: sending updated cues: %s', current_cues)
                remove_plan_cue_window.destroy()
                self.pco_plan.create_and_update_plan_app_cues(note_content=json.dumps(current_cues))
                self.main_ui_window.reload()

            Button(remove_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Remove',
                   command=lambda: (current_cues.pop(listbox.curselection()[0]), listbox.delete(first=listbox.curselection()[0]))).pack(side=LEFT)
            Button(remove_plan_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay',
                   command=okay).pack(side=RIGHT)

    def __add_global_cue(self):
        self.utilities_menu.destroy()
        self.cue_handler_global.create_cues()

    def __remove_global_cue(self):
        logger.debug('Utilities.__remove_global_cue clicked')
        self.utilities_menu.destroy()

        global_cues = []

        with open('global_cues.json', 'r') as f:
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

            with open('global_cues.json', 'w') as f:
                f.writelines(json.dumps(global_cues))

            self.main_ui_window.reload()

        Button(remove_global_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Remove',
               command=lambda: (
               global_cues.pop(listbox.curselection()[0]), listbox.delete(first=listbox.curselection()[0]))).pack(
            side=LEFT)

        Button(remove_global_cue_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay',
               command=okay).pack(side=RIGHT)

    def __add_device(self):
        pass


class MainUI:
    def __init__(self, startup):

        self.startup = startup

        # service info
        self.service_type_id = self.startup.service_type_id
        self.service_id = self.startup.service_id

        # class initiations
        self.pco_live = PcoLive(service_type_id=self.service_type_id, plan_id=self.service_id)
        self.pco_plan = PcoPlan(service_type=self.service_type_id, plan_id=self.service_id)
        self.cue_handler = CueCreator(ui=self, startup=startup, devices=startup.devices)
        self.cue_handler_global = CueCreator(ui=self, startup=startup, devices=startup.devices, cue_type='global')
        self.cue_handler_plan = CueCreator(ui=self, startup=startup, devices=startup.devices, cue_type='plan')
        self.kipro_ui = KiProUi()
        self.kipro = KiPro()
        self.qlxd = None

        self.plan_items = self.pco_plan.get_service_items()[1]

        self.previous_item_index = None
        self.current_item_index = 0
        self.next_item_index = None

        self.current_live_item_id = self.pco_live.get_current_live_item()

        # get + set index of current live item
        for item in self.plan_items:
            if item['id'] == self.current_live_item_id:
                self.current_item_index = item['sequence']

        # plan view data variables
        self.time_remaining_is_positive = True
        self.current_item_timer_input = 0
        self.adjacent_plan_current_item = None
        self.adjacent_plan_next_item = None
        self.adjacent_plan_timer_input = 0
        self.adjacent_plan_time_remaining_is_positive = True

        # plan windows
        self.plan_window = Toplevel()

        # plan window frames
        self.reminder_frame = Frame(self.plan_window, bg=bg_color)
        self.clock_frame = Frame(self.plan_window, bg=bg_color)

        self.adjacent_plan_frame = Frame(self.clock_frame, bg=bg_color)
        self.aux_controls_frame = Frame(self.plan_window, bg=bg_color)
        self.kipro_control_frame = Frame(self.plan_window, bg=bg_color)
        self.plan_cues_frame = Frame(self.plan_window, bg=bg_color)
        self.current_service_frame = Frame(self.plan_window, bg=bg_color)
        self.qlxd_frame = Frame(self.plan_window, bg=bg_color)

        self.service_controls_frame = Frame(self.plan_window, bg=bg_color)
        self.next_previous_frame = Frame(self.service_controls_frame, bg=bg_color)

        self.gear_icon = PhotoImage(file=os.path.join(abs_path, 'gear_icon_gray.png'))
        self.gear_icon = self.gear_icon.subsample(12, 12)

        self.item_frames = []
        self.item_time_labels = []
        self.item_spacer_labels = []
        self.item_title_labels = []
        self.item_person_labels = []
        self.item_producer_note_labels = []
        self.item_app_cue_labels = []
        self.item_advance_cue_labels = []

        #scrollbar for plan items frame (service_plan_frame)
        self.plan_items_canvas = Canvas(self.plan_window, bg=bg_color, width=plan_item_frame_width, height=plan_item_view_height, highlightthickness=0)
        self.items_view_scrollbar = None

        self.service_plan_frame = Frame(self.plan_items_canvas, bg=bg_color)

        self.plan_items_canvas.create_window(0, 0, anchor='nw', window=self.service_plan_frame)


        self.plan_items_canvas.grid(row=2, column=0)


        # height of all plan item frames added together
        self.service_plan_frame_height = None


        self.progress_bar = None

        self.auto_advance_cancelled_by_user = False
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

        #  if global_cues.json exists, read. If file does not exist, variable is set to None
        self.global_cues = []
        if os.path.exists(os.path.join(abs_path, 'global_cues.json')):
            with open('global_cues.json', 'r') as f:
                self.global_cues = json.loads(f.read())

        self.global_cues = None if len(self.global_cues) == 0 else self.global_cues  # reset global_cues variable back to None if it's empty

        if enable_webserver:
            self.webserver_thread = None
            self.__start_webserver()

        # pprint.pprint(self.plan_items)

    def build_plan_window(self):
        self.plan_window.title('Service Control')
        self.plan_window.configure(bg=bg_color)

        self.__build_current_service_time()
        # self.__build_time_remaining_progress_bar()
        self.__build_auto_advance_reminder_ui()
        self.__build_clock()
        self.__build_item_timer()
        self.__build_items_view()
        self.__build_aux_controls()

        if self.global_cues is not None:
            self.__build_global_cues_button()

        self.__build_utilities_button()
        if display_kipros:
            self.__build_kipro_status()

        self.__build_plan_cue_buttons()
        self.update_live()

        contains_qlxd = False
        for device in self.startup.devices:
            if device['type'] == 'shure_qlxd':
                contains_qlxd = True
                break

        if contains_qlxd:
            self.__build_qlxd_ui()

        self.__cleanup()
        self.plan_window.mainloop()

    def update_item_timer(self, time):
        self.time_remaining_is_positive = True
        self.current_item_timer_input = time

    def next(self, cue_items, from_web=False):
        logger.debug('Next button pressed')
        self.update_item_timer(time=self.plan_items[self.next_item_index]['length'])

        if cue_items:
            self.__cue()

        self.pco_live.go_to_next_item()
        self.update_live()

        if enable_webserver is True and not from_web:
            logger.debug('MainUI.next: sending next command to webserver')
            next_web_data = {'action': 'app_next'}
            requests.post('http://127.0.0.1/action', json=json.dumps(next_web_data))

    def previous(self, cue_items, from_web=False):
        self.update_item_timer(time=self.plan_items[self.previous_item_index]['length'])

        if cue_items:
            self.__cue(next=False)

        self.pco_live.go_to_previous_item()
        self.update_live()

        if not from_web and enable_webserver is True:
            logger.debug('MainUI.next: sending previous command to webserver')
            previous_web_data = {'action': 'app_previous'}
            requests.post('http://127.0.0.1/action', json=json.dumps(previous_web_data))

    def update_live(self, service_time=False):
        # Get index of current live item
        current_live_item_id = self.pco_live.get_current_live_item()

        # Colors CURRENT live item
        # Normally, we would configure each label/frame item separately, but if the label doesn't exist for that item, the source list
        # contains None. Adding None makes the index consistent across lists.
        # Each action has it's own try/except loop, because if we configured all labels at the same time, a single exception
        # would stop at the exception, skipping all labels after it


        for item in self.plan_items:
            if item['id'] == current_live_item_id:
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
                    self.item_advance_cue_labels[item['sequence'] - 1]
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
                self.item_advance_cue_labels[index]
            ]
            return labels


        is_first_item = False
        is_last_item = False

        if self.current_item_index == 1:
            logger.debug('Current live item is the first plan item, id %s', current_live_item_id)
            is_first_item = True

        if self.current_item_index == len(self.plan_items):
            logger.debug('Current live item is the last plan item, id %s', current_live_item_id)
            is_last_item = True


        self.previous_item_index = find_previous_item(self.current_item_index-1)
        self.next_item_index = find_next_item(self.current_item_index-1)

        # logger.debug('Previous item index: %s, %s, Next item index: %s, %s',
        #               self.previous_item_index, self.plan_items[self.previous_item_index]['title'], self.next_item_index, self.plan_items[self.next_item_index]['title'])


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
            self.__build_current_service_time()

    def update_adjacent_plan(self, current, next, length):
        logger.debug('update_adjacent_plan: Got new items: current: %s, next: %s, time: %s', current, next, length)
        self.adjacent_plan_current_item.configure(text=current)
        self.adjacent_plan_next_item.configure(text=next)

        self.adjacent_plan_time_remaining_is_positive = True
        self.adjacent_plan_timer_input = length

    def build_adjacent_plan(self, topo, current, next, length):
        logger.debug('build_adjacent_plan: topo: %s, current: %s, next: %s, time: %s', topo, current, next, length)

        self.adjacent_plan_timer_input = length

        self.adjacent_plan_frame.pack()

        adjacent_plan_topo = Label(self.adjacent_plan_frame, bg=bg_color, fg=text_color, text=topo, font=(font, other_text_size-3))
        current_label = Label(self.adjacent_plan_frame, bg=bg_color, fg=text_color, text='Current Item', font=(font, other_text_size-4))
        next_label = Label(self.adjacent_plan_frame, bg=bg_color, fg=text_color, text='Next Item', font=(font, other_text_size-4))
        self.adjacent_plan_current_item = Label(self.adjacent_plan_frame, bg=bg_color, fg=text_color, text=current, font=(font, other_text_size))
        self.adjacent_plan_next_item = Label(self.adjacent_plan_frame, bg=bg_color, fg=text_color, text=next, font=(font, other_text_size))

        adjacent_plan_topo.grid(row=0, column=0)
        current_label.grid(row=1, column=0)
        next_label.grid(row=1, column=1)
        self.adjacent_plan_current_item.grid(row=2, column=0)
        self.adjacent_plan_next_item.grid(row=2, column=1)

        timer_label = Label(self.adjacent_plan_frame, bg=bg_color, fg=clock_text_color, font=(clock_text_font, 15))
        timer_label.grid(row=1, column=2)

        def tick():
            if self.adjacent_plan_timer_input == 0:
                self.adjacent_plan_time_remaining_is_positive = False

            if not self.adjacent_plan_time_remaining_is_positive:
                self.adjacent_plan_timer_input += 1
                timer_label.configure(fg=clock_overrun_color)
            else:
                self.adjacent_plan_timer_input -= 1
                timer_label.configure(fg=clock_text_color)

            time_string = time.strftime('%M:%S', time.gmtime(self.adjacent_plan_timer_input))
            timer_label.configure(text=time_string)

            self.adjacent_plan_frame.after(1000, tick)
        tick()

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

    def reload(self):
        # self.webserver_thread.join() #todo stop webserver thread
        self.plan_window.destroy()
        self.kipro_ui.kill_threads()
        reloaded_ui = MainUI(startup=self.startup)
        reloaded_ui.build_plan_window()

    def __start_webserver(self):
        self.webserver_thread = threading.Thread(target=lambda: fs.start(startup_class=self.startup))
        # while
        self.webserver_thread.start()

    def __build_time_remaining_progress_bar(self):
        self.progress_bar = Canvas(self.plan_window)
        if self.time_remaining_is_positive:
            self.progress_bar.configure(height=3, bg=accent_color_1)
        self.progress_bar.grid(row=10, column=0, sticky='w')

    def __build_current_service_time(self):
        logger.debug('Building current service time info')
        current_service_time = self.pco_plan.get_current_live_service()
        if not current_service_time is None:
            logger.debug('Live service info: %s', current_service_time)
            self.current_service_frame.grid(row=0, column=0, sticky='w')
            Label(self.current_service_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Current Live Service:  ').grid(row=0, column=0)
            Label(self.current_service_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text=current_service_time['local']).grid(row=0, column=1)

    def __set_advance_to_next_reminder(self):
        pass

    def __build_clock(self): # also checks for advance to next cues on each tick
        time_label = Label(self.clock_frame,
                           fg=clock_text_color,
                           bg=bg_color,
                           font=(clock_text_font, clock_text_size))
        self.clock_frame.grid(row=1, column=0, sticky='w')
        time_label.pack(side=LEFT)

        def tick():

            time_string = time.strftime('%H:%M:%S')
            time_label.config(text=time_string)
            time_label.after(1000, tick)

            current_item_notes = self.plan_items[self.current_item_index-1]['notes']

            if 'App Cues' in current_item_notes:
                for cue in current_item_notes['App Cues']:
                    if cue['uuid'] == advance_on_next_uuid and len(cue['times']) > 0: # advance to next cue exists in current item
                        current_time = dt.datetime.now().time()
                        current_time_in_seconds = (current_time.hour * 3600) + (current_time.minute * 60) + current_time.second

                        def cue_time_to_seconds(cue_time_list):
                            return (int(cue_time_list[0]) * 3600) + (int(cue_time_list[1]) * 60) + (int(cue_time_list[2]))

                        def find_difference(cue_time):
                            return cue_time_to_seconds(cue_time)-current_time_in_seconds

                        soonest_advance_time_index = 0
                        for iteration, cue_time in enumerate(cue['times'], start=0):
                            difference = find_difference(cue_time)
                            if difference < 0:
                                pass
                            else:
                                current_smallest_time = find_difference(cue['times'][soonest_advance_time_index])
                                if current_smallest_time < 0:
                                    soonest_advance_time_index = iteration
                                else:
                                    if difference < current_smallest_time:
                                            soonest_advance_time_index = iteration

                        countdown = find_difference(cue['times'][soonest_advance_time_index])
                        if countdown == 0 and not self.auto_advance_cancelled_by_user: #advance to next
                            logger.info(f'Auto advancing to next because of cue: {cue}')
                            self.next(cue_items=True)
                        if countdown == 0:
                            self.auto_advance_cancelled_by_user = False
                            self.auto_advance_reminder_frame.place_forget()
                        elif countdown in list(range(30)) and not self.auto_advance_cancelled_by_user:
                            self.auto_advance_reminder_label.configure(text=f'Advancing to next item in {countdown} seconds')
                            self.auto_advance_reminder_frame.place(relx=.5, rely=.45, anchor=CENTER)

        tick()

    def __build_auto_advance_reminder_ui(self):
        self.auto_advance_reminder_frame = Frame(self.plan_window, bg=accent_color_1)
        self.auto_advance_reminder_label = Label(self.auto_advance_reminder_frame, fg=reminder_color, bg=accent_color_1, font=(font, reminder_font_size))
        self.auto_advance_reminder_label.grid(row=0, column=0)

        def cancel():
            self.auto_advance_cancelled_by_user = True
            self.auto_advance_reminder_frame.place_forget()

        Button(self.auto_advance_reminder_frame, bg=accent_color_1, fg=reminder_color, font=(font, reminder_font_size), text='CANCEL', command=cancel).grid(row=0, column=1)

    def __build_item_timer(self):
        time_label = Label(self.clock_frame,
                           fg=clock_text_color,
                           bg=bg_color,
                           font=(clock_text_font, clock_text_size))
        time_label.pack(side=LEFT, padx=50)

        def tick():
            current_item_length = int(self.plan_items[self.current_item_index - 1]['length'])
            try:
                percentage = 1 - self.current_item_timer_input/current_item_length
            except ZeroDivisionError:
                pass

            if self.time_remaining_is_positive and self.progress_bar is not None:
                self.progress_bar.configure(width=percentage*plan_item_frame_width)

            if self.current_item_timer_input == 0:
                self.time_remaining_is_positive = False

            if not self.time_remaining_is_positive:
                self.current_item_timer_input += 1
                time_label.configure(fg=clock_overrun_color)
            else:
                self.current_item_timer_input -= 1
                time_label.configure(fg=clock_text_color)

            time_string = time.strftime('%M:%S', time.gmtime(self.current_item_timer_input))
            time_label.configure(text=time_string)

            self.clock_frame.after(1000, tick)
        tick()

    def __build_utilities_button(self):
        Button(self.clock_frame, bg=bg_color, image=self.gear_icon, command=lambda:
               Utilities(main_ui_window_init=self).open_utilities_menu()).pack(side=RIGHT, padx=15)

    def __build_global_cues_button(self):
        Button(self.clock_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
               text='Global Cues', command=self.__open_global_cues_menu).pack(side=RIGHT, padx=15)

    def __open_global_cues_menu(self):
        if self.global_cues is not None:
            global_cues_menu = Tk()
            global_cues_menu.title('Global Cues')
            global_cues_menu.configure(bg=bg_color)

            def if_close():
                if close_global_cues_menu_after_cue:
                    global_cues_menu.destroy()

            for cue in self.global_cues:
                Button(global_cues_menu, bg=bg_color, fg=text_color, font=(font, other_text_size+2), text=cue[0], padx=30, pady=5,
                       command=lambda cue = cue: (self.cue_handler_global.activate_cues(cues=cue[1]), if_close())).pack()

    def __build_items_view(self):

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
            separator.pack_propagate(0)
            separator.pack()

            frame.pack_propagate(0)
            frame.pack()

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
                for cue in self.cue_handler.verbose_decode_cues(cuelist=item['notes']['App Cues']):
                    label_text = f'{label_text}{cue}\n'
                label = Label(frame, bg=bg_color, fg=text_color, text=label_text, justify=LEFT,
                      font=(font, app_cue_font_size))
                self.item_app_cue_labels.append(label)
                label.place(anchor='nw', x=1050)

                # if number of cues on an item is greater than 4, increase height of item frame so nothing is cut off
                number_of_cues = len(self.cue_handler.verbose_decode_cues(cuelist=item['notes']['App Cues']))
                if number_of_cues > 2:
                    over = number_of_cues - 2
                    height = 28 + (10 * over)
                    frame.configure(height=height)
                    logger.debug(f'{item["title"]} height: {height}, {frame.winfo_height()}')

            else:
                self.item_app_cue_labels.append(None)

        # Item auto advance labels
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'App Cues' in item['notes']:
                advance_cue_times = []
                for cue in item['notes']['App Cues']:
                    if cue['uuid'] == advance_on_next_uuid:
                        for advance_time in cue['times']:
                            advance_cue_times.append(advance_time)

                        auto_advance_label = Label(frame, bg=bg_color, fg=text_color, font=(font, app_cue_font_size + 1),
                                                   justify=LEFT)
                        auto_advance_label.place(anchor='nw', x=900)

                if len(advance_cue_times) == 0:
                    self.item_advance_cue_labels.append(None)
                else:
                    self.item_advance_cue_labels.append(auto_advance_label)

                advance_time_text = ''
                for iteration, advance_time in enumerate(advance_cue_times):
                    advance_time_text += f'ADVANCE TO NEXT AT {advance_time[0]}:{advance_time[1]}:{advance_time[2]}'
                    if not iteration + 1 == len(advance_cue_times):
                        advance_time_text += '\n'
                    auto_advance_label.configure(text=advance_time_text)
            else:
                self.item_advance_cue_labels.append(None)

        # Item 'options' button
        for item, frame in zip(self.plan_items, self.item_frames):
            if not item['type'] == 'header':
                Button(frame, image=self.gear_icon, anchor='w', font=(font, options_button_text_size),
                       bg=bg_color, fg=text_color, command=lambda item=item:
                    CueCreator(startup=self.startup, ui=self, devices=self.startup.devices).create_cues(input_item=item)
                    ).pack(side=RIGHT)

    def __build_kipro_status(self):
        self.kipro_control_frame.grid(row=2, column=2, sticky='n')

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

    def __build_qlxd_ui(self):
        self.qlxd = ShureQLXDUi(devices=self.startup.devices, ui=self)
        self.qlxd_frame.grid(row=5, column=0, sticky='e')
        self.qlxd_frame.configure(height=60, width=plan_item_frame_width)

        threading.Thread(target=self.qlxd.main_loop).start()

    def __build_plan_cue_buttons(self):
        if self.pco_plan.check_if_plan_app_cue_exists():
            logger.debug('MainUI.__build_plan_cue_buttons: adding plan cue buttons')
            self.plan_cues_frame.grid(row=3, column=0)
            self.plan_cues = self.pco_plan.get_plan_app_cues()
            for iteration, cue in enumerate(self.plan_cues):
                cue_name = cue[0]
                cue_data = cue[1]
                logger.debug('Creating plan cues button: %s, cue_data = %s', cue_name, cue_data)
                Button(self.plan_cues_frame, bg=bg_color, fg=text_color, font=(font, other_text_size),
                       text=cue_name, command=lambda cue_data=cue_data: self.cue_handler.activate_cues(cue_data)).grid(row=0, column=iteration, padx=plan_cue_pad_x, pady=10)
        else:
            logger.debug('No plan cues were added because none were found')

    def __build_aux_controls(self):
        self.aux_controls_frame.grid(row=4, column=0)
        self.aux_controls_frame.configure(height=60, width=plan_item_frame_width)

        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Previous (no actions)', font=(accent_text_font, 10), command=lambda: self.previous(cue_items=False)).grid(row=1, column=1, padx=next_previous_pad_x)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Previous', font=(accent_text_font, accent_text_size), command=lambda: self.previous(cue_items=True)).grid(row=1, column=2, padx=next_previous_pad_x)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Next', font=(accent_text_font, accent_text_size), command=lambda: self.next(cue_items=True)).grid(row=1, column=3, padx=next_previous_pad_x)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Next (no actions)', font=(accent_text_font, 10), command=lambda: self.next(cue_items=False)).grid(row=1, column=4, padx=next_previous_pad_x)

    def __on_mousewheel(self, event):
        self.plan_items_canvas.yview_scroll(math.floor(-1*(int(event.delta))/120), 'units')

    def __cleanup(self):
        self.service_plan_frame_height = 0 if self.service_plan_frame_height is None else self.service_plan_frame_height

        for frame in self.item_frames:  # find height of all item frames together, used to pass to the plan frame before creation of the scrollbar
            frame.update()
            height = frame.winfo_height()
            self.service_plan_frame_height += height
        logger.debug('service_plan_frame height is %s', self.service_plan_frame_height)

        self.service_plan_frame.configure(height=self.service_plan_frame_height)
        self.items_view_scrollbar = Scrollbar(self.plan_window, command=self.plan_items_canvas.yview)
        self.plan_items_canvas.configure(scrollregion=self.plan_items_canvas.bbox('all'), yscrollcommand=self.items_view_scrollbar.set)
        self.items_view_scrollbar.grid(row=2, column=1, sticky='nsw')

        self.service_plan_frame.bind_all('<MouseWheel>', self.__on_mousewheel)


    def __cue(self, next=True):
        # Called when next or previous functions are called. it will cue actions on the next item when next=True,
        # cues actions on previous items when next=False
        logger.debug('__cue called, next=%s', next)
        if next:
            if 'App Cues' in self.plan_items[self.next_item_index]['notes']:
                logger.debug('App cues found in %s, sending to cue_handler: %s', self.plan_items[self.next_item_index]['title'], self.plan_items[self.next_item_index]['notes']['App Cues'])
                self.cue_handler.activate_cues(cues=self.plan_items[self.next_item_index]['notes']['App Cues'])

                for cue in self.plan_items[self.next_item_index]['notes']['App Cues']:
                    if cue['uuid'] == 'b652b57e-c426-4f83-87f3-a7c4026ec1f0': # reminder
                        time = (int(cue['minutes']) * 60) + int(cue['seconds'])
                        self.__set_reminder(reminder_time = time, reminder_text=cue['reminder'])
        if not next:
            if 'App Cues' in self.plan_items[self.previous_item_index]['notes']:
                logger.debug('App cues found in %s, sending to cue_handler: %s', self.plan_items[self.previous_item_index]['title'], self.plan_items[self.previous_item_index]['notes']['App Cues'])
                self.cue_handler.activate_cues(cues=self.plan_items[self.previous_item_index]['notes']['App Cues'])

                for cue in self.plan_items[self.previous_item_index]['notes']['App Cues']:
                    if cue['uuid'] == 'b652b57e-c426-4f83-87f3-a7c4026ec1f0': # reminder
                        time = (int(cue['minutes']) * 60) + int(cue['seconds'])
                        self.__set_reminder(reminder_time = time, reminder_text=cue['reminder'])

    def __set_reminder(self, reminder_time, reminder_text):
        reminder_frame = Frame(self.plan_window, bg=accent_color_1)

        Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text=reminder_text, font=(font, reminder_font_size)).grid(row=0, column=1)
        Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text='REMINDER:  ',font=(accent_text_font, accent_text_size)).grid(row=0, column=0)
        Button(reminder_frame, fg=reminder_color, bg=accent_color_1, text='clear', font=(accent_text_font, accent_text_size), command=reminder_frame.destroy).grid(row=0, column=2)

        def show_reminder():
            logger.debug('Showing reminder %s', reminder_text)
            reminder_frame.place(relx=.5, rely=.5, anchor=CENTER)

        reminder_frame.after(reminder_time*1000, show_reminder)


class AdjacentPlanView:
    def __init__(self, ui):
        self.adjacent_service = SelectService(send_to=self)
        self.service_type_id = None
        self.service_id = None

        self.pco_plan = None
        self.pco_live = None

        self.adjacent_plan_details = None
        self.adjacent_plan_items = None
        self.adjacent_plan_type_details = None

        self.current_live_id = None

        self.ui = ui

    def ask_adjacent_plan(self):
        logger.debug('AdjacentPlanView.ask_adjacent_plan: asking which plan to load')
        self.adjacent_service.ask_service_info()

    def receive_plan_details(self, service_type_id, service_id):
        logger.debug('AdjacentPlanView: Received adjacent plan: %s, %s', service_type_id, service_id)
        self.service_type_id = service_type_id
        self.service_id = service_id

        self.__create_adjacent_plan_details()

    def __create_adjacent_plan_details(self):
        self.pco_plan = PcoPlan(service_type=self.service_type_id, plan_id=self.service_id)
        self.pco_live = PcoLive(service_type_id=self.service_type_id, plan_id=self.service_id)

        self.adjacent_plan_details = self.pco_plan.get_service_details_from_id()[1]
        self.adjacent_plan_items = self.pco_plan.get_service_items()[1]
        self.adjacent_plan_type_details = self.pco_plan.get_service_type_details_from_id()[1]

        service_topo = self.adjacent_plan_type_details + ' > ' + self.adjacent_plan_details['date']
        if not self.adjacent_plan_details['title'] is None:
            service_topo += ' | ' + self.adjacent_plan_details['title']

        self.current_live_id = self.pco_live.get_current_live_item()

        for item in self.adjacent_plan_items:
            if item['id'] == self.current_live_id:
                current_live_item_title = item['title']
                current_live_item_time = item['length']
            else:
                current_live_item_title = 'Not Currently Live'
                current_live_item_time = 0

        next_item = self.pco_live.find_next_live_item()

        if not next_item is None:
            next_item_title = ['title']
        else:
            next_item_title = ''

        self.ui.build_adjacent_plan(topo=service_topo, current=current_live_item_title, next=next_item_title, length=current_live_item_time)

        self.__recheck(interval=adjacent_plan_refresh_interval)

    def __recheck(self, interval):

        def send_new(current, next, length):
            self.ui.update_adjacent_plan(current=current, next=next, length=length)

        def check():
            logger.debug('Checking if adjacent plan has updated')
            recheck_live_id = self.pco_live.get_current_live_item()
            if not recheck_live_id == self.current_live_id:
                for item in self.adjacent_plan_items:
                    if item['id'] == recheck_live_id:
                        current = item['title']
                        length = item['length']
                        next_title = self.pco_live.find_next_live_item()['title']
                        send_new(current=current, next=next_title, length=length)
            threading.Thread(target=sleep_and_check).start()

        def sleep_and_check():
            time.sleep(interval)
            check()
        check()


class KiProUi:
    def __init__(self):
        self.kipro = KiPro()
        self.exit_event = threading.Event()

    def kill_threads(self):
        logger.debug('KiProUi.kill_threads: setting exit event')
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
            threading.Thread(name='kipro_refresh', target=lambda: self.__refresh(interval=kipro_update_interval, ui=ui)).start()

    def __refresh(self, interval, ui):
        # logger.debug(f'KiProUi.__refresh: exit_event.is_set(): {self.exit_event.is_set()}')

        time.sleep(interval)
        if not self.exit_event.is_set():
            self.update_kipro_status(ui=ui)
        else:
            logger.debug('KiProUi.__refresh: exit event set, stopping loop')


class ShureQLXDUi:
    def __init__(self, devices, ui):
        self.devices = devices
        self.main_ui = ui

        self.qlxd_class_inits = []
        self.qlxd_device_names = []

        self.qlxd_channel_boxes = []
        self.qlxd_box_names = []
        self.qlxd_box_rf_labels = []
        self.qlxd_box_rf_levels = []
        self.qlxd_box_audio_labels = []
        self.qlxd_box_audio_levels = []
        self.qlxd_box_battery_levels = []
        self.battery_icon_canvases = []

        self.battery_levels = None
        self.metering_data = None

        for device in devices:
            if device['type'] == 'shure_qlxd':
                self.qlxd_class_inits.append(ShureQLXD(ip=device['ip_address']))
                for name in device['channel_names']:
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

        self.__start_all_metering()
        self.__create_channel_boxes()

        self.loop_counter = 0

    def __create_channel_boxes(self):
        for _ in self.qlxd_device_names:
            f = Frame(self.main_ui.qlxd_frame, bg=bg_color, width=100, height=50)
            f.pack_propagate(0)
            f.pack(side=LEFT, padx=5, pady=10)
            self.qlxd_channel_boxes.append(f)

        for box, channel_info in zip(self.qlxd_channel_boxes, self.qlxd_device_names):  # Channel name labels
            name = Label(box, bg=bg_color, fg=text_color, text=channel_info, font=(font, 9))
            self.qlxd_box_names.append(name)
            name.place(x=0, y=0)

        for box in self.qlxd_channel_boxes: # channel RF labels
            r = Label(box, bg=bg_color, fg=text_color, text='RF:', font=(font, 6))
            self.qlxd_box_rf_labels.append(r)
            r.place(x=0, y=20)

        for box in self.qlxd_channel_boxes: # channel RF strength
            r = Label(box, bg=bg_color, fg='#ffffff', text='', font=(font, 3))
            self.qlxd_box_rf_levels.append(r)
            r.place(x=24, y=23)

        for box in self.qlxd_channel_boxes: # channel audio labels
            r = Label(box, bg=bg_color, fg=text_color, text='AUD:', font=(font, 6))
            self.qlxd_box_audio_labels.append(r)
            r.place(x=0, y=33)

        for box in self.qlxd_channel_boxes:  # channel audio strength
            r = Label(box, bg=bg_color, fg='#ffffff', text='', font=(font, 3))
            self.qlxd_box_audio_levels.append(r)
            r.place(x=24, y=36)

        for box in self.qlxd_channel_boxes:
            b = Label(box, image=self.battery_images[0], bg=bg_color)
            self.qlxd_box_battery_levels.append(b)
            b.place(x=63, y=0)

    def __start_all_metering(self):
        for init in self.qlxd_class_inits:
            init.start_all_metering()

    def __stop_all_metering(self):
        for init in self.qlxd_class_inits:
            init.stop_all_metering()

    def __get_battery_levels(self):
        data = []
        for init in self.qlxd_class_inits:
            results = init.check_battery_levels()
            for result in results:
                data.append(result)
        return data

    def __get_metering_results(self):
        data = []
        for init in self.qlxd_class_inits:
            results = init.get_meter_info()
            for result in results:
                data.append(result)
        return data

    def __update_ui_rf_and_audio(self, levels):
        total_characters_in_progress_bar = 36
        for channel, rf_label, aud_label in zip(levels, self.qlxd_box_rf_levels, self.qlxd_box_audio_levels):
            try:
                characters_in_rf = round(int(channel['rf_level']) * (total_characters_in_progress_bar/115))
                rf_str = ''
                for _ in range(characters_in_rf):
                    rf_str += '#'
                rf_label.configure(text=rf_str)

                characters_in_aud = round(int(channel['audio_level']) * (total_characters_in_progress_bar / 15))
                aud_str = ''
                for _ in range(characters_in_aud):
                    aud_str += '#'
                aud_label.configure(text=aud_str)
            except TypeError:
                pass

    def __update_battery_ui(self, levels):
        for level, box_image in zip(levels, self.qlxd_box_battery_levels):
            try:
                box_image.configure(image=self.battery_images[level+1])
            except IndexError:
                box_image.configure(image=self.battery_images[0])

    def main_loop(self):
        self.__stop_all_metering()
        self.__start_all_metering()

        while True:
            # logger.debug(f'loop counter: {self.loop_counter}')
            if self.loop_counter == 0:
                # logger.debug('Checking battery levels')
                self.battery_levels = self.__get_battery_levels()
                self.__update_battery_ui(levels=self.battery_levels)

                self.__start_all_metering()

            self.metering_data = self.__get_metering_results()
            self.__update_ui_rf_and_audio(levels=self.metering_data)

            iteration = 0
            for level, battery in zip(self.metering_data, self.battery_levels):
                try:
                    if int(level['rf_level']) < 40 or battery == 255:
                        self.qlxd_channel_boxes[iteration].configure(bg=live_color)
                        self.qlxd_box_names[iteration].configure(bg=live_color)
                        self.qlxd_box_rf_labels[iteration].configure(bg=live_color)
                        self.qlxd_box_rf_levels[iteration].configure(bg=live_color)
                        self.qlxd_box_audio_labels[iteration].configure(bg=live_color)
                        self.qlxd_box_audio_levels[iteration].configure(bg=live_color)
                        self.qlxd_box_battery_levels[iteration].configure(bg=live_color)

                    elif int(level['rf_level']) > 40 and battery <= 2:
                        self.qlxd_channel_boxes[iteration].configure(bg='#bf7831')
                        self.qlxd_box_names[iteration].configure(bg='#bf7831')
                        self.qlxd_box_rf_labels[iteration].configure(bg='#bf7831')
                        self.qlxd_box_rf_levels[iteration].configure(bg='#bf7831')
                        self.qlxd_box_audio_labels[iteration].configure(bg='#bf7831')
                        self.qlxd_box_audio_levels[iteration].configure(bg='#bf7831')
                        self.qlxd_box_battery_levels[iteration].configure(bg='#bf7831')

                    else:
                        self.qlxd_channel_boxes[iteration].configure(bg=kipro_idle_color)
                        self.qlxd_box_names[iteration].configure(bg=kipro_idle_color)
                        self.qlxd_box_rf_labels[iteration].configure(bg=kipro_idle_color)
                        self.qlxd_box_rf_levels[iteration].configure(bg=kipro_idle_color)
                        self.qlxd_box_audio_labels[iteration].configure(bg=kipro_idle_color)
                        self.qlxd_box_audio_levels[iteration].configure(bg=kipro_idle_color)
                        self.qlxd_box_battery_levels[iteration].configure(bg=kipro_idle_color)

                    iteration += 1

                except TypeError:
                    pass

                if self.loop_counter == 20:
                    self.loop_counter = 0
                else:
                    self.loop_counter += 1



class Main:  #startup
    def __init__(self):
        os.chdir(abs_path)

        if os.path.exists('devices.json'):
            logger.debug('devices.json exists, reading...')
            with open('devices.json', 'r') as f:
                self.devices = json.loads(f.read())
        else:
            logger.warning('Did not find devices.json file')
            DeviceEditor().build_default_file()
            with open('devices.json', 'r') as f:
                self.devices = json.loads(f.read())

        self.main_service = SelectService()
        self.main_service.ask_service_info()

        self.service_type_id = self.main_service.service_type_id
        self.service_id = self.main_service.service_id

        self.main_ui = MainUI(startup=self)

        self.main_ui.build_plan_window()

start = Main()

