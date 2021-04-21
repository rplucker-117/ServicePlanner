# import requests
from tkinter import *
from tkinter import messagebox
# import json
from settings import *
import time
# import pprint
import logging
# import datetime
from pco_plan import PcoPlan
from pco_live import PcoLive
# from cue_coder import cue_coder
from tkinter import ttk
import threading
from kipro import kipro
from cue_creator import CueCreator


logging.basicConfig(level=log_level)
logging.getLogger('urllib3').setLevel(logging.WARNING)


class SelectService:
    def __init__(self, send_to):
        self.service_type_id = None
        self.service_id = None

        self.service_types_menu = Tk()
        self.services_menu = Tk()
        self.services_menu.withdraw()
        self.pco_plan = PcoPlan()

        self.send_to = send_to

    def ask_service_info(self):
        self.__build_service_types_menu()

    def __build_service_types_menu(self):
        self.service_types_menu.title('Pick service folder')
        self.service_types_menu.configure(bg=bg_color)

        # Create button for each service type, call build_service_types_menu when clicked
        for service_type in self.pco_plan.get_service_types()[1]:
            Button(self.service_types_menu, text=service_type['name'],
                   command=lambda
                 service_type=service_type: self.__build_services_menu(
                 service_type_id=service_type['id']),
                   bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1, width=50,
                   pady=3).pack()
        self.service_types_menu.mainloop()

    def __build_services_menu(self, service_type_id):
        self.service_types_menu.destroy()

        self.service_type_id = service_type_id
        self.services_menu.deiconify()

        self.services_menu.title('Pick Service')
        self.services_menu.configure(bg=bg_color)
        self.pco_plan = PcoPlan(service_type=service_type_id)

        #Create button for each service within service type, call build_plan_window + destroy root when clicked
        for service in self.pco_plan.get_services_from_service_type()[1]:
            Button(self.services_menu, text=service['date'], command=lambda service=service: self.__update_values(id=service['id']),
                   bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1, width=50,
                   pady=3, ).pack()

    def __update_values(self, id):
        self.services_menu.destroy()
        self.service_id = id
        logging.debug('SelectService: service_type_id: %s, service_id: %s', self.service_type_id, self.service_id)
        if not self.send_to is None:
            self.send_to.receive_plan_details(service_type_id=self.service_type_id, service_id=self.service_id)

class Utilities:
    def __init__(self, main_ui_window_init):
        self.main_ui_window = main_ui_window_init
        self.cue_handler = CueCreator(service_type_id = self.main_ui_window.service_type_id, plan_id=self.main_ui_window.service_id)
        self.pco_live = PcoLive(service_type_id = self.main_ui_window.service_type_id, plan_id=self.main_ui_window.service_id)
        self.pco_plan = PcoPlan(service_type = self.main_ui_window.service_type_id, plan_id=self.main_ui_window.service_id)

        self.utilities_menu = Tk()

    def open_utilities_menu(self):
        self.utilities_menu.geometry('400x250')
        self.utilities_menu.configure(bg=bg_color)

        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Start Live Service', font=(font, other_text_size), command=self.__start_live).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Advance to Next Service', font=(font, other_text_size), command=self.__advance_to_next_service).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Reload Plan', font=(font, other_text_size), command=self.__reload_plan).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Load Adjacent Plan', font=(font, other_text_size), command=self.__load_adjacent).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Format Kipros', font=(font, other_text_size), command=self.__format).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Download Kipro Clips', font=(font, other_text_size), command=self.__download).pack()
        Button(self.utilities_menu, bg=bg_color, fg=text_color, text='Add Global Cue', font=(font, other_text_size), command=self.__add_global).pack()

        self.utilities_menu.mainloop()

    def __start_live(self):
        if self.pco_live.get_current_live_item() is None:
            self.pco_live.go_to_next_item()
            self.utilities_menu.destroy()
            self.main_ui_window.update_live()

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
        self.main_ui_window.update_live()

        self.utilities_menu.destroy()

    def __reload_plan(self):
        reload()

    def __load_adjacent(self):
        self.utilities_menu.destroy()
        adjacent_plan = AdjacentPlanView()
        adjacent_plan.ask_adjacent_plan()


    def __format(self):
        yes_no = messagebox.askyesno('Format KiPros', message="Are you sure you want to format ALL KiPros?")
        if yes_no:
            for kipro_unit in kipros_new[1:]:
                kipro.format_current_slot(ip=kipro_unit['ip'])

        self.utilities_menu.destroy()

    def __download(self):
        pass

    def __add_global(self):
        pass

class MainUI:
    def __init__(self, service_type_id, service_id):

        # service info
        self.service_type_id = service_type_id
        self.service_id = service_id

        # class initiations
        self.pco_live = PcoLive(service_type_id=service_type_id, plan_id=service_id)
        self.pco_plan = PcoPlan(service_type=service_type_id, plan_id=service_id)
        self.cue_handler = CueCreator(service_type_id=service_type_id, plan_id=service_id)

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
        self.service_plan_frame = Frame(self.plan_window, bg=bg_color)
        self.adjacent_plan_frame = Frame(self.clock_frame, bg=bg_color)
        self.aux_controls_frame = Frame(self.plan_window, bg=bg_color)
        self.kipro_control_frame = Frame(self.plan_window, bg=bg_color)

        self.service_controls_frame = Frame(self.plan_window, bg=bg_color)
        self.global_cues_frame = Frame(self.service_controls_frame, bg=bg_color)
        self.next_previous_frame = Frame(self.service_controls_frame, bg=bg_color)

        self.gear_icon = PhotoImage(file=r"gear_icon_gray.png")
        self.gear_icon = self.gear_icon.subsample(12, 12)

        self.item_frames = []
        self.item_time_labels = []
        self.item_spacer_labels = []
        self.item_title_labels = []
        self.item_person_labels = []
        self.item_producer_note_labels = []
        self.item_app_cue_labels = []

        self.kipro_buttons = []
        self.kipro_storage_remaining_bars = []

    def build_plan_window(self):

        self.plan_window.title('Service Control')
        self.plan_window.configure(bg=bg_color)

        self.__build_clock()
        self.__build_utilities_button()
        self.__build_item_timer()
        self.__build_items_view()
        self.__build_aux_controls()
        self.__build_kipro_status()

        self.update_live()

        self.plan_window.mainloop()

    def update_item_timer(self, time):
        self.time_remaining_is_positive = True
        self.current_item_timer_input = time

    def next(self, cue_items):
        logging.debug('Next button pressed')
        self.update_item_timer(time=self.plan_items[self.next_item_index]['length'])

        if cue_items:
            self.__cue()

        self.pco_live.go_to_next_item()
        self.update_live()


    def previous(self, cue_items):
        self.update_item_timer(time=self.plan_items[self.previous_item_index]['length'])

        if cue_items:
            self.__cue()

        self.pco_live.go_to_previous_item()
        self.update_live()

    def update_live(self):
        # Get index of current live item
        current_live_item_id = self.pco_live.get_current_live_item()

        # Colors CURRENT live item
        # Normally, we would configure each label/frame item separately, but if the label doesn't exist for that item, the source list
        # contains None. Adding None makes the index consistent across lists.
        # Each action has it's own try/except loop, because if we configured all labels at the same time, a single exception
        # would stop at the exception, skipping all labels after it


        for item in self.plan_items:
            if item['id'] == current_live_item_id:
                logging.debug('Current live item is index %s, %s', item['sequence'], item['title'])

                live_index = item['sequence']

                self.current_item_index = live_index

                labels_to_update = [
                    self.item_frames[item['sequence'] - 1],
                    self.item_time_labels[item['sequence'] - 1],
                    self.item_spacer_labels[item['sequence'] - 1],
                    self.item_title_labels[item['sequence'] - 1],
                    self.item_person_labels[item['sequence'] - 1],
                    self.item_producer_note_labels[item['sequence'] - 1],
                    self.item_app_cue_labels[item['sequence'] - 1]
                ]

                for label in labels_to_update:
                    try:
                        label.configure(bg=live_color)
                    except AttributeError:
                        continue

        def find_previous_item(i):
            if not self.plan_items[i-1]['type'] == 'header':
                logging.debug('__update_live: find_previous_item: returning %s', i)
                return i-1
            else:
                return find_previous_item(i-1)

        def find_next_item(i):
            if not self.plan_items[i+1]['type'] == 'header':
                logging.debug('__update_live: find_next_item: returning %s', i)
                return i+1
            else:
                return find_next_item(i+1)

        def define_labels_to_change(index):
            labels = [
                self.item_frames[index],
                self.item_time_labels[index],
                self.item_spacer_labels[index],
                self.item_title_labels[index],
                self.item_person_labels[index],
                self.item_producer_note_labels[index],
                self.item_app_cue_labels[index]
            ]
            return labels

        self.previous_item_index = find_previous_item(self.current_item_index-1)
        self.next_item_index = find_next_item(self.current_item_index-1)

        logging.debug('Previous item index: %s, %s, Next item index: %s, %s',
                      self.previous_item_index, self.plan_items[self.previous_item_index]['title'], self.next_item_index, self.plan_items[self.next_item_index]['title'])

        for previous_item, next_item in zip(define_labels_to_change(self.previous_item_index), define_labels_to_change(self.next_item_index)):
            try:
                previous_item.configure(bg=bg_color)
            except AttributeError:
                pass
            try:
                next_item.configure(bg=bg_color)
            except AttributeError:
                pass

    def update_adjacent_plan(self, current, next, length):
        logging.debug('update_adjacent_plan: Got new items: current: %s, next: %s, time: %s', current, next, length)
        self.adjacent_plan_current_item.configure(text=current)
        self.adjacent_plan_next_item.configure(text=next)

        self.adjacent_plan_time_remaining_is_positive = True
        self.adjacent_plan_timer_input = length

    def build_adjacent_plan(self, topo, current, next, length):
        logging.debug('build_adjacent_plan: topo: %s, current: %s, next: %s, time: %s', topo, current, next, length)

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
        logging.debug('Got kipro status: unit: %s, status: %s', kipro_unit, status)

        if status == 1:
            self.kipro_buttons[kipro_unit].configure(bg=kipro_idle_color)
        elif status == 2:
            self.kipro_buttons[kipro_unit].configure(bg=kipro_recording_color)
        else:
            self.kipro_buttons[kipro_unit].configure(bg=kipro_error_color)

    def update_kipro_storage(self, kipro_unit, percent):
        self.kipro_storage_remaining_bars[kipro_unit].configure(value=percent)

    def __build_kipro_status(self):
        self.kipro_control_frame.grid(row=1, column=1, sticky='n')

        for kipro_unit in kipros_new[1:]:
            button = Button(self.kipro_control_frame, text=kipro_unit['name'], font=(font, other_text_size), fg=text_color, height=2, relief=FLAT,
                            command=lambda kipro_unit=kipro_unit: kipro.toggle_start_stop(ip=kipro_unit['ip'], name=kipro_unit['name'], include_date=True))
            self.kipro_buttons.append(button)

        for kipro_unit in kipros_new[1:]:
            progress = ttk.Progressbar(self.kipro_control_frame, length=110, mode='determinate', maximum=100)
            self.kipro_storage_remaining_bars.append(progress)

        for button, progress in zip(self.kipro_buttons, self.kipro_storage_remaining_bars):
            button.pack()
            progress.pack()

        KiPro().update_kipro_status()

    def __build_clock(self):
        time_label = Label(self.clock_frame,
                           fg=clock_text_color,
                           bg=bg_color,
                           font=(clock_text_font, clock_text_size))
        self.clock_frame.grid(row=0, column=0, sticky='w')
        time_label.pack(side=LEFT)

        def tick():
            time_string = time.strftime('%H:%M:%S')
            time_label.config(text=time_string)
            time_label.after(1000, tick)

        tick()

    def __build_item_timer(self):
        time_label = Label(self.clock_frame,
                           fg=clock_text_color,
                           bg=bg_color,
                           font=(clock_text_font, clock_text_size))
        time_label.pack(side=LEFT, padx=50)

        def tick():
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

    def __build_items_view(self):
        self.service_plan_frame.grid(row=1, column=0)

        # Item frames
        for item in self.plan_items:
            # Add item frames to list
            if item['type'] == 'header':
                item_frame_height = 20
                item_frame_color = header_color
            else:
                item_frame_height = 40
                item_frame_color = bg_color
            item_frame = Frame(self.service_plan_frame, bg=item_frame_color, width=plan_item_frame_width, height=item_frame_height)
            self.item_frames.append(item_frame)

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
                label.place(anchor='nw', x=500)
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
                label.place(anchor='nw', x=650)
            else:
                self.item_app_cue_labels.append(None)

        # Item 'options' button
        for item, frame in zip(self.plan_items, self.item_frames):
            if not item['type'] == 'header':
                Button(frame, image=self.gear_icon, anchor='w', font=(font, options_button_text_size),
                       bg=bg_color, fg=text_color, command=lambda item=item:
                    CueCreator(service_type_id=main_service.service_type_id, plan_id=main_service.service_id).create_cues(input_item=item)
                    ).pack(side=RIGHT)

    def __build_aux_controls(self):
        self.aux_controls_frame.grid(row=2, column=0)
        self.aux_controls_frame.configure(height=60, width=plan_item_frame_width)
        # self.aux_controls_frame.grid_propagate(0)

        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Previous (no actions)', font=(accent_text_font, 10), command=lambda: self.previous(cue_items=False)).grid(row=0, column=1)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Previous', font=(accent_text_font, accent_text_size), command=lambda: self.previous(cue_items=True)).grid(row=0, column=2)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Next', font=(accent_text_font, accent_text_size), command=lambda: self.next(cue_items=True)).grid(row=0, column=3)
        Button(self.aux_controls_frame, bg=accent_color_1, fg=accent_text_color, text='Next (no actions)', font=(accent_text_font, 10), command=lambda: self.next(cue_items=False)).grid(row=0, column=4)

    def __cue(self):
        logging.debug('__cue called')
        if 'App Cues' in self.plan_items[self.next_item_index]['notes']:
            logging.debug('App cues found in %s, sending to cue_handler: %s', self.plan_items[self.next_item_index]['title'], self.plan_items[self.next_item_index]['notes']['App Cues'])
            self.cue_handler.activate_cues(cues=self.plan_items[self.next_item_index]['notes']['App Cues'])

            for cue in self.plan_items[self.next_item_index]['notes']['App Cues']:
                if cue['device'] == 'Reminder':
                    time = (int(cue['minutes']) * 60) + int(cue['seconds'])
                    self.__set_reminder(reminder_time = time, reminder_text=cue['reminder'])

    def __set_reminder(self, reminder_time, reminder_text):
        reminder_frame = Frame(self.plan_window, bg=accent_color_1)

        Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text=reminder_text, font=(font, reminder_font_size)).grid(row=0, column=0)
        Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text='REMINDER:  ',font=(accent_text_font, accent_text_size)).grid(row=0, column=1)
        Button(reminder_frame, fg=reminder_color, bg=accent_color_1, text='clear', font=(accent_text_font, accent_text_size), command=reminder_frame.destroy).grid(row=0, column=2)

        def show_reminder():
            logging.debug('Showing remidner %s', reminder_text)
            reminder_frame.place(relx=.5, rely=.5, anchor=CENTER)

        reminder_frame.after(reminder_time*1000, show_reminder)

class AdjacentPlanView:
    def __init__(self):
        self.adjacent_service = SelectService(send_to=self)
        self.service_type_id = None
        self.service_id = None

        self.pco_plan = None
        self.pco_live = None

        self.adjacent_plan_details = None
        self.adjacent_plan_items = None
        self.adjacent_plan_type_details = None

        self.current_live_id = None

    def ask_adjacent_plan(self):
        logging.debug('AdjacentPlanView.ask_adjacent_plan: asking which plan to load')
        self.adjacent_service.ask_service_info()

    def receive_plan_details(self, service_type_id, service_id):
        logging.debug('AdjacentPlanView: Received adjacent plan: %s, %s', service_type_id, service_id)
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

        next_item_title = self.pco_live.find_next_live_item()['title']

        main_ui.build_adjacent_plan(topo=service_topo, current=current_live_item_title, next=next_item_title, length=current_live_item_time)

        self.__recheck(interval=adjacent_plan_refresh_interval)

    def __recheck(self, interval):

        def send_new(current, next, length):
            main_ui.update_adjacent_plan(current=current, next=next, length=length)

        def check():
            logging.debug('Checking if adjacent plan has updated')
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

class KiPro:
    def __init__(self):
        pass

    def update_kipro_status(self):
        for iteration, kipro_unit in enumerate(kipros_new[1:]):

            status = int(kipro.get_status(ip=kipro_unit['ip']))
            logging.debug('update_kipro_status: status is %s for kipro %s', status, kipro_unit['name'])
            main_ui.update_kipro_status(kipro_unit=iteration, status=status)

            percent = int(kipro.get_remaining_storage(ip=kipro_unit['ip']))
            logging.debug('update_kipro_status: storage is %s percent for kipro %s', percent, kipro_unit['name'])
            main_ui.update_kipro_storage(kipro_unit=iteration, percent=percent)

        threading.Thread(target=lambda: self.__refresh(interval=10)).start()


    def __refresh(self, interval):
        time.sleep(interval)
        self.update_kipro_status()

def startup():
    global main_service
    global main_ui

    main_service = SelectService(send_to=None)
    main_service.ask_service_info()

    main_ui = MainUI(service_type_id=main_service.service_type_id, service_id=main_service.service_id)
    main_ui.build_plan_window()


def reload():
    startup()


if __name__ == '__main__':
    startup()
