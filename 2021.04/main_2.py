import requests
from tkinter import *
import json
from settings import *
from cue_creator import cue_creator_window
import time
import pprint
import logging
import datetime
from pco_plan import pco_plan_update
from pco_live import pco_live
from cue_coder import cue_coder
from tkinter import ttk
import threading
from kipro import kipro

logging.basicConfig(level=log_level)

plan_main_info = {
    'folder_id': None,
    'plan_id': None,
    'plan_index': None
}

adjacent_plan_data = {
    'service_type_name': '',
    'service_date': '',
    'service_title': '',
    'service_item_data': '',
    'next_item_title': '',
    'current_item_title': '',
    'current_item_id': '',
    'current_item_time_remaining': 0,
    'time_remaining_is_positive': True,
    'item_has_updated': False
}

#Update adjacent plan info
def update_adjacent_plan_info(service_type_id, service_id, refresh):
    live_item_id = pco_live.get_current_live_item(service_type=service_type_id, plan=service_id)
    next_item_id = pco_live.find_next_live_item(service_type_id=service_type_id, service_id=service_id)['id']

    #find if adjacent plan has advanced to next item, update current item time remaining if so. For use in countdown clock
    stated_live_id = adjacent_plan_data['current_item_id']
    if not live_item_id == stated_live_id:
        logging.debug('update_adjacent_plan_info: live item has changed')
        adjacent_plan_data['time_remaining_is_positive'] = True
        for item in adjacent_plan_data['service_item_data']:
            if item['id'] == live_item_id:
                adjacent_plan_data['current_item_time_remaining'] = int(item['length'])
                logging.debug('update_adjacent_plan_info: updated current_item_time_remaining to %s', item['length'])

    #set current live item id
    adjacent_plan_data['current_item_id'] = live_item_id

    #find current item title
    for item in adjacent_plan_data['service_item_data']:
        if item['id'] == live_item_id:
            logging.debug('update_adjacent_plan_info: Found current item title: %s', item['title'])
            adjacent_plan_data['current_item_title'] = item['title']
            if adjacent_plan_data['item_has_updated']:
                adjacent_plan_data['current_item_time_remaining'] = item['length']

    #find next item title
    for item in adjacent_plan_data['service_item_data']:
        if item['id'] == next_item_id:
            logging.debug('update_adjacent_plan_info: Found next item title: %s', item['title'])
            adjacent_plan_data['next_item_title'] = item['title']

    if refresh:
        time.sleep(adjacent_plan_refresh_interval)
        update_adjacent_plan_info(service_type_id = service_type_id, service_id = service_id, refresh=True)


class Startup:
    def __init__(self):
        pass

    def build_service_types_menu(self):
        service_types_menu = Tk()
        service_types_menu.title('Pick service folder')
        service_types_menu.configure(bg=bg_color)

        # Create button for each service type, call build_service_types_menu when clicked
        for service_type in pco_plan_update.get_service_types()[1]:
            Button(service_types_menu, text=service_type['name'],
                   command=lambda
                 service_type=service_type: (Startup().build_services_menu(
                 service_type_id=service_type['id']), service_types_menu.destroy()),
                   bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1, width=50,
                   pady=3).pack()
        service_types_menu.mainloop()

    def build_services_menu(self, service_type_id):
        services_menu = Tk()
        services_menu.title('Pick Service')
        services_menu.configure(bg=bg_color)
        #Create button for each service within service type, call build_plan_window + destroy root when clicked
        for service in pco_plan_update.get_services_from_service_type(service_type_id=service_type_id)[1]:
            Button(services_menu, text=service['date'],
                command=lambda service=service: (Startup().call_main_ui(service_type_id=service_type_id, service_id=service['id']),
                                                 services_menu.destroy()), bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1, width=50,
                     pady=3).pack()

    def call_main_ui(self, service_type_id, service_id):
        main_ui = MainUI(service_type_id=service_type_id, service_id=service_id)
        main_ui.build_plan_window()

class MainUI:
    def __init__(self, service_type_id, service_id):
        # service info
        self.plan_items = pco_plan_update.get_service_items(service_type_id=service_type_id, service_id=service_id)[1]
        self.service_type_id = service_type_id
        self.service_id = service_id

        # plan view data variables
        self.current_item_timer_input = None

        # plan windows
        self.plan_window = Tk()

        # plan window frames
        self.reminder_frame = Frame(self.plan_window, bg=bg_color)
        self.clock_frame = Frame(self.plan_window, bg=bg_color)
        self.service_plan_frame = Frame(self.plan_window, bg=bg_color)
        self.adjacent_plan_frame = Frame(self.plan_window, bg=bg_color)
        self.aux_controls_frame = Frame(self.plan_window, bg=bg_color)

        self.service_controls_frame = Frame(self.plan_window, bg=bg_color)
        self.global_cues_frame = Frame(self.service_controls_frame, bg=bg_color)
        self.next_previous_frame = Frame(self.service_controls_frame, bg=bg_color)

        self.item_frames = []


    def build_plan_window(self):

        self.plan_window.title('Service Control')
        self.plan_window.configure(bg=bg_color)

        self.start_clock()
        self.build_items_view()

    def start_clock(self):
        time_label = Label(self.clock_frame,
                           fg=clock_text_color,
                           bg=bg_color,
                           font=(clock_text_font, clock_text_size))
        self.clock_frame.grid(row=0, column=0, sticky='w')
        time_label.pack(side=LEFT)

        def tick():
            time_string = time.strftime('%H:%M:%S %p')
            time_label.config(text=time_string)
            time_label.after(1000, tick)

        tick()

    def build_items_view(self):
        self.service_plan_frame.grid(row=1, column=0)

        item_titles = []

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
                Label(frame, bg=bg_color, fg=text_color, font=(font, item_time_size), text=time_str).pack(side=LEFT)

        # Spacer between item times and item titles
        for item, frame in zip(self.plan_items, self.item_frames):
            if not item['type'] == 'header':
                Label(frame, bg=bg_color, font=(font, item_time_size), text='').pack(side=LEFT)

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
            Label(frame, bg=bg, fg=fg, text=item['title'], font=(font, title_size)).pack(side=LEFT)

        # Item people
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'Person' in item['notes']:
                Label(frame, bg=bg_color, fg=text_color, text=item['notes']['Person'], font=(font, plan_text_size-2)).place(anchor='nw', x=400)

        # Item producer notes
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'Producer Notes' in item['notes']:
                Label(frame, bg=bg_color, fg=text_color, text=item['notes']['Producer Notes'], font=(font, producer_note_text_size)).place(anchor='nw', x=500)

        # Item app cues
        for item, frame in zip(self.plan_items, self.item_frames):
            if 'App Cues' in item['notes']:
                label_text = ''
                for cue in cue_coder.cue_verbose_decoder(cuedict=item['notes']['App Cues']):
                    label_text = f'{label_text}{cue}\n'
                Label(frame, bg=bg_color, fg=text_color, text=label_text, justify=LEFT,
                      font=(font, app_cue_font_size)).place(anchor='nw', x=650)

        # Item 'options' button
        for item, frame in zip(self.plan_items, self.item_frames):
            if not item['type'] == 'header':
                Button(frame, text='options', anchor='w', font=(font, options_button_text_size),
                       bg=bg_color, fg=text_color, command=lambda item=item: cue_creator_window(
                        type='item',
                        plan_items=self.plan_items,
                        item_index=item['sequence'],
                        service_type=self.service_type_id,
                        plan_id =self.service_id
                    )).pack(side=RIGHT)


Startup().build_service_types_menu()


# looks at which item is live, updates ui accordingly. Does not pull item details down again, unlike reload_ui_all()
def create_ui(plan_items):


    logging.debug('starting clock')

    logging.debug('clock started')

    plan_window.title('Service Plan')
    service_plan_frame = Frame(plan_window, bg=bg_color, bd=2)

    def set_reminder(reminder_time, reminder):
        reminder_frame = Frame(plan_window, bg=accent_color_1)
        reminder_message_label = Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text=reminder,
                                       font=(font, reminder_font_size))
        reminder_title = Label(reminder_frame, fg=reminder_color, bg=accent_color_1, text='REMINDER:  ',
                               font=(accent_text_font, accent_text_size))
        clear_button = Button(reminder_frame, fg=reminder_color, bg=accent_color_1, text='clear',
                              font=(accent_text_font, accent_text_size), command=reminder_frame.destroy)

        reminder_title.grid(row=0, column=0)
        reminder_message_label.grid(row=0, column=1)
        clear_button.grid(row=0, column=2)
        def show_reminder():
            logging.debug('Showing reminder %s', reminder)
            reminder_frame.grid(row=1, column=0)

        reminder_message_label.after(reminder_time*1000, show_reminder)

    tk_item_titles = []
    tk_item_person_tags = []
    tk_item_producer_note_tags = []
    tk_item_app_cue_tags = []
    tk_options_buttons = []

    # find longest item title, for use in label width below
    title_lengths = []
    for item in plan_items:
        title_lengths.append(len(plan_items[item]['item_title']))
    max_title_length = max(title_lengths)

    # find length of longest person tag, for use in label width below
    people_lengths = []
    for item in plan_items:
        person = plan_items[item]['person']
        if person == None:
            person = ''
        people_lengths.append(len(person))
    max_person_length = max(people_lengths)

    # find length of longest producer note, for use in label width below
    producer_note_lengths = []
    for item in plan_items:
        note = plan_items[item]['producer_notes']
        if note == None:
            note = ''
        producer_note_lengths.append(len(note))
    max_producer_note_length = max(producer_note_lengths)



    # add plan item titles to grid
    logging.debug('adding item titles')
    for iteration, item in enumerate(plan_items):
        tk_item_titles.append(Label(plan_item_frames[iteration], text=plan_items[iteration]['item_title'],
                                    anchor='w', font=(item_font, plan_text_size), bg=bg_color, fg=text_color, width=25))

        # check if item is song, style it if true
        if plan_items[iteration]['item_type'] == 'song':
            tk_item_titles[iteration].configure(fg=song_title_color, font=(song_font, plan_text_size), bg=bg_color)

        # check if item is header, style it if true
        if plan_items[iteration]['item_type'] == 'header':
            tk_item_titles[iteration].configure(fg=text_color, bg=header_color, font=(font, header_font_size))

        # add item titles to grid
        tk_item_titles[iteration].grid(row=0, column=0, sticky='w')

    logging.debug('adding plan people')
    # add plan people, works the same as above
    for iteration, item in enumerate(plan_items):
        tk_item_person_tags.append(Label(plan_item_frames[iteration], text=plan_items[iteration]['person'],
                                         font=(font, plan_text_size), bg=bg_color, fg=text_color,
                                         justify=LEFT, anchor='w', width=max_person_length))

        if plan_items[iteration]['item_type'] == 'header':
            tk_item_person_tags[iteration].configure(bg=header_color, font=(font, header_font_size))

        tk_item_person_tags[iteration].grid(row=0, column=1, sticky='w')

    logging.debug('adding plan producer notes')
    # add plan producer notes
    for iteration, item in enumerate(plan_items):
        tk_item_producer_note_tags.append(Label(plan_item_frames[iteration], text=plan_items[iteration]['producer_notes'],
                                                anchor='w', font=(font, producer_note_text_size), bg=bg_color,
                                                fg=text_color, justify=LEFT,
                                                wraplength=275, width=40))
        if plan_items[iteration]['item_type'] == 'header':
            tk_item_producer_note_tags[iteration].configure(bg=header_color, font=(font, header_font_size),
                                                            width=max_producer_note_length)

        tk_item_producer_note_tags[iteration].grid(row=0, column=2, sticky='w')

    # add plan app cues to display. Visual only.
    for iteration, item in enumerate(plan_items):
        tk_item_app_cue_tags.append(Label(plan_item_frames[iteration],
                                          text=plan_items[iteration]['app_cues_verbose'],
                                          font=(font, app_cue_font_size), bg=bg_color,
                                          fg=text_color, justify=LEFT))

        tk_item_app_cue_tags[iteration].grid(row=0, column=3)

    def options_button_pressed(item_index):
        logging.debug('options button pressed')
        cue_creator_window(type='item',
                           plan_items=plan_items,
                           item_index=item_index,
                           service_type=plan_main_info['folder_id'],
                           plan_id=plan_main_info['plan_id'],)

    # add options button to each item
    for iteration, item in enumerate(plan_items):
        if not plan_items[iteration]['item_type'] == 'header':
            logging.debug('adding options button for item %s', plan_items[iteration]['item_title'])
            tk_options_buttons.append(Button(service_plan_frame, text='options',
                                             anchor='w', font=(font, options_button_text_size),
                                             bg=bg_color, fg=text_color,
                                             command=lambda iteration=iteration: options_button_pressed(iteration)))
        else:
            tk_options_buttons.append(Label(service_plan_frame,
                                            bg=bg_color, font=(font, header_font_size)))

        tk_options_buttons[iteration].grid(row=iteration, column=4, sticky='w')



    #refresh the ui colors based on live item. Makes 2 api calls total, called upn every next or previous
    def refresh_live_ui():
        # id of current live item
        live_id = pco_live.get_current_live_item(service_type=plan_main_info['folder_id'],
                                                 plan=plan_main_info['plan_id'])

        # find active live id in items_master dict
        def find_live():
            logging.debug('Finding live item index for id %s', live_id)
            for iteration, item in enumerate(items_master):
                if items_master[iteration]['item_id'] == live_id:
                    logging.debug('live index is %s', iteration)
                    return iteration
        global live_item_index
        live_item_index = find_live()
        logging.debug(f"current live item index is {live_item_index},"
                      f"{plan_items[live_item_index]['item_title']}")

        # re-styles all plan items based on header status
        for tk_item in (tk_item_titles, tk_item_person_tags, tk_item_producer_note_tags,
                                          tk_item_app_cue_tags, plan_item_frames):
            for iteration, item in enumerate(tk_item):
                if not iteration == live_item_index:
                    if not items_master[iteration]['item_type'] == 'header':
                        item.configure(bg=bg_color)
                    else:
                        item.configure(bg=header_color)


        # Countdown clock based on time remaining. Total time is retreived from items_master above
        # global declaration is needed below for next() and previous(). When called, they destroy time_remaining_label
        # to prevent creating a new one
        global time_remaining_label
        global current_live_item_title
        time_remaining_label = Label(clock_frame,
                                     fg=clock_text_color,
                                     bg=bg_color,
                                     font=(clock_text_font, clock_text_size))

        # lets also create a spacer with a | between the time and countdown timer
        Label(clock_frame, text= '  |  ',
              fg=clock_text_color,
              bg=bg_color, font=('Arial', clock_text_size)).grid(row=0, column=1)

        time_remaining_label.grid(row=0, column=2)

        time_remaining = int(items_master[live_item_index]['item_length'])
        time_remaining_is_positive = True
        logging.debug('Current time remaining in %s : %s', items_master[live_item_index]['item_title'], time_remaining)
        def live_item_timer():
            nonlocal time_remaining
            nonlocal time_remaining_is_positive

            # Check if time_remaining is 0, change time_remaingin_is_positive to false + change color if so.
            if time_remaining == 0:
                logging.debug('time remaining is negative. counting upwards')
                time_remaining_is_positive = False
                time_remaining_label.config(fg=clock_overrun_color)

            # count downwards if remaining time is positive
            if time_remaining_is_positive:
                time_remaining -= 1

            # count upwards if remaining time is negative
            if not time_remaining_is_positive:
                time_remaining += 1

            #format string time
            time_remaining_formatted = time.strftime('%M:%S', time.gmtime(time_remaining))

            # add - to front if negative
            if not time_remaining_is_positive:
                time_remaining_formatted = '-' + time_remaining_formatted

            # apply text to label, reschedule to repeat in 1s
            time_remaining_label.config(text=str(time_remaining_formatted))
            time_remaining_label.after(1000, live_item_timer)

        live_item_timer()

        # another spacer between live item timer and live item
        Label(clock_frame, text=' | ',
              fg=clock_text_color,
              bg=bg_color, font=('Arial', clock_text_size)).grid(row=0, column=3)

        # show current live item next to current live item timer
        current_live_item_title = Label(clock_frame,
              text=items_master[live_item_index]['item_title'],
              bg=bg_color,
              fg=clock_text_color,
              font=(clock_text_font, clock_section_live_item_text_size))
        if items_master[live_item_index]['item_type'] == 'song':
            current_live_item_title.config(fg=song_title_color)
        current_live_item_title.grid(row=0, column=4)



        # styles items with live color scheme based on live item index
        tk_item_titles[live_item_index].configure(bg=live_color)
        tk_item_person_tags[live_item_index].configure(bg=live_color)
        tk_item_producer_note_tags[live_item_index].configure(bg=live_color)
        tk_item_app_cue_tags[live_item_index].configure(bg=live_color)
        plan_item_frames[live_item_index].configure(bg=live_color)

    def add_global_cue():
        # get current cues
        logging.debug('add_global_cue clicked')
        # get plan note id for app_cue category
        plan_note_id = pco_plan_update.get_plan_app_cue_note_id(service_type=plan_main_info['folder_id'], plan=plan_main_info['plan_id'])[0]
        logging.debug('add_global_cue: plan_note_id is %s', plan_note_id)
        # pass app cue note id to get_plan_note_content, returns a dict
        current_global_cues = pco_plan_update.get_plan_note_content(service_type=plan_main_info['folder_id'], plan=plan_main_info['plan_id'], note_id = plan_note_id)
        # call cue_creator_window
        cue_creator_window(type='global',
                           plan_items=current_global_cues,
                           item_index='App Cues',
                           service_type=plan_main_info['folder_id'],
                           plan_id=plan_main_info['plan_id'])

    # load another plan next to current one for viewing only. To keep track of multi-campus plans running in parallel
    def load_adjacent_plan():
        logging.debug('load_adjacent_plan called.')

        def select_service_from_list(service_type_id):
            logging.debug('load_adjacent_plan: select_service_from_list: service_type_id: %s', service_type_id)
            adjacent_plan_service_pick_window = Tk()
            adjacent_plan_service_pick_window.configure(bg=bg_color)

            services = pco_plan_update.get_services_from_service_type(service_type_id=service_type_id)[1]
            for service in services:
                Button(adjacent_plan_service_pick_window, text=service['date'],
                       bg=bg_color, fg=text_color, font=(font, other_text_size),
                       bd=1, width=50, pady=3,
                       command=lambda id = service['id']: (
                           logging.debug('load_adjacent_plan: select_service_from_list: button pressed. Service id %s', id),
                           adjacent_plan_service_pick_window.destroy(),
                           create_adjacent_plan_view(service_type_id=service_type_id, service_id=id)
                       )).pack()


        def create_adjacent_plan_view(service_type_id, service_id):
            adjacent_plan_frame = Frame(plan_window, bg=bg_color)
            adjacent_plan_frame.grid(row=0, column=2)

            update_adjacent_plan_info(service_type_id=service_type_id, service_id=service_id, refresh=False)

            service_type_name = pco_plan_update.get_service_type_details_from_id(service_type_id=service_type_id)[1]
            service_data = pco_plan_update.get_service_details_from_id(service_type_id=service_type_id,
                                                                       service_id=service_id)

            service_item_data = pco_plan_update.get_service_items(service_type_id=service_type_id,
                                                                  service_id=service_id)[1]

            adjacent_plan_data['service_type_name'] = service_type_name
            adjacent_plan_data['service_date'] = service_data[1]['date']
            adjacent_plan_data['service_title'] = service_data[1]['title']
            adjacent_plan_data['service_item_data'] = service_item_data

            # service topography
            service_topo_text = ''
            if not adjacent_plan_data['service_title'] is None:
                service_topo_text = adjacent_plan_data['service_type_name'] + '  >  ' + adjacent_plan_data['service_date'] + '  |  ' + adjacent_plan_data['service_title']
            else:
                service_topo_text = adjacent_plan_data['service_type_name'] + '  >  ' + adjacent_plan_data['service_date']

            service_topo_text_label = Label(adjacent_plan_frame, fg=text_color, bg=bg_color, text=service_topo_text,
                  font=(font, options_button_text_size))
            service_topo_text_label.grid(row=0, column=0)

            # current item label label
            current_item_label_label = Label(adjacent_plan_frame, fg=text_color, bg=bg_color, text='Current item:',
                  font=(font, options_button_text_size))
            current_item_label_label.grid(row=1, column=0)

            # next item label label
            next_item_label_label = Label(adjacent_plan_frame, fg=text_color, bg=bg_color, text='Next item:',
                  font=(font, options_button_text_size))
            next_item_label_label.grid(row=1, column=1)

            # current item label
            current_item_label = Label(adjacent_plan_frame, fg=text_color, bg=bg_color,
                                       font=(font, plan_text_size))
            current_item_label.grid(row=2, column=0)

            # next item label
            next_item_label = Label(adjacent_plan_frame, fg=text_color, bg=bg_color,
                                    font=(font, plan_text_size))
            next_item_label.grid(row=2, column=1)

            current_item_timer = Label(adjacent_plan_frame, fg=clock_text_color, bg=bg_color,
                                       font=(font, plan_text_size))
            current_item_timer.grid(row=0, column=1)

            def refresh():
                current_item_label.configure(text=adjacent_plan_data['current_item_title'])
                next_item_label.configure(text=adjacent_plan_data['next_item_title'])

                if adjacent_plan_data['current_item_time_remaining'] == 0:
                    adjacent_plan_data['time_remaining_is_positive'] = False
                    logging.debug('Adjacent plan clock time is negative. Counting upwards')

                if adjacent_plan_data['time_remaining_is_positive']:
                    adjacent_plan_data['current_item_time_remaining'] -= 1
                    current_item_timer.config(fg=clock_text_color)
                else:
                    current_item_timer.config(fg=clock_overrun_color)
                    adjacent_plan_data['current_item_time_remaining'] += 1

                current_item_timer.configure(text=time.strftime('%M:%S',
                                                         time.gmtime(adjacent_plan_data['current_item_time_remaining'])))

                adjacent_plan_frame.after(1000, refresh)
            refresh()

            t1 = threading.Thread(target=lambda: update_adjacent_plan_info(service_type_id=service_type_id, service_id=service_id, refresh=True))
            t1.start()

        adjacent_plan_service_type_pick_window = Tk()
        adjacent_plan_service_type_pick_window.configure(bg=bg_color)

        service_types = pco_plan_update.get_service_types()[1]
        for service_type in service_types:
            Button(adjacent_plan_service_type_pick_window, text=service_type['name'],
                                         bg=bg_color, fg=text_color, font=(font, other_text_size),
                                         bd=1, width=50, pady=3,
                   command=lambda id = service_type['id']: (select_service_from_list(service_type_id=id),
                                    adjacent_plan_service_type_pick_window.destroy())).pack()

    # when next button is pressed
    def next(cue_items):
        if cue_items:
            # Finds next item that's not a header, for use in cueing before making api calls. Cues are activated instantly
            # instead of waiting on internet connection/api calls
            def find_next_item(iteration):
                logging.debug(f'finding next item. iteration {iteration}')
                if not plan_items[live_item_index + iteration]['item_type'] == 'header':
                    logging.debug(f"Next item that's not a header is: {live_item_index + iteration},"
                                  f" {plan_items[live_item_index + iteration]['item_title']}, "
                                  f"app cues: {plan_items[live_item_index + iteration]['app_cues']}")
                    return int(live_item_index + iteration)
                else:
                    logging.debug('next item is a header. running again.')
                    if iteration > len(plan_items):
                        pass
                    else:
                        return find_next_item(iteration + 1)

            next_item = find_next_item(1)
            if not plan_items[next_item]['app_cues'] is None:
                logging.debug('Passing app cues to cue_coder.cue_decoder(). %s', plan_items[next_item]['app_cues'])
                cue_coder.cue_decoder(cuedict=plan_items[next_item]['app_cues'])
                reminder = cue_coder.reminder_decoder(cuedict=plan_items[next_item]['app_cues'])
                if not reminder is None:
                    set_reminder(reminder_time=reminder[1], reminder=reminder[0])
            else:
                logging.debug('No app cues on next item.')

        logging.debug('moving to next item')
        pco_live.take_control(service_type=plan_main_info['folder_id'], plan=plan_main_info['plan_id'])
        pco_live.go_to_next_item(service_type=plan_main_info['folder_id'], plan=plan_main_info['plan_id'])
        logging.debug('destroying time_remaining timer')
        time_remaining_label.destroy()
        current_live_item_title.destroy()
        refresh_live_ui()

    # when previous button is pressed
    def previous(cue_items):
        if cue_items:
            def find_previous_item(iteration):
                logging.debug(f'finding previous item. iteration {iteration}')
                if not plan_items[live_item_index - iteration]['item_type'] == 'header':
                    logging.debug(f"previous item that's not a header is: {live_item_index - iteration},"
                                  f" {plan_items[live_item_index - iteration]['item_title']}, "
                                  f"app cues: {plan_items[live_item_index - iteration]['app_cues']}")
                    return int(live_item_index - iteration)
                else:
                    logging.debug('previous item is a header. running again.')
                    if iteration > len(plan_items):
                        pass
                    else:
                        return find_previous_item(iteration + 1)

            previous_item = find_previous_item(1)
            if not plan_items[previous_item]['app_cues'] is None:
                logging.debug('Passing app cues to cue_coder.cue_decoder(). %s', plan_items[previous_item]['app_cues'])
                cue_coder.cue_decoder(cuedict=plan_items[previous_item]['app_cues'])
                reminder = cue_coder.reminder_decoder(cuedict=plan_items[previous_item]['app_cues'])
                if not reminder is None:
                    set_reminder(reminder_time=reminder[1], reminder=reminder[0])
            else:
                logging.debug('No app cues on next item.')

        logging.debug('moving to previous item')
        pco_live.take_control(service_type=plan_main_info['folder_id'], plan=plan_main_info['plan_id'])
        pco_live.go_to_previous_item(service_type=plan_main_info['folder_id'], plan=plan_main_info['plan_id'])
        logging.debug('destroying time_remaining timer')
        time_remaining_label.destroy()
        current_live_item_title.destroy()
        refresh_live_ui()

    # right aux controls pane
    aux_controls_frame = Frame(plan_window, bg=bg_color)

    # add reload ui button to top of window. For use in reloading plan from pco after cues have been added
    reload = Button(aux_controls_frame, text='Reload Entire Plan',
                    anchor='w', font=(font, options_button_text_size),
                    bg=bg_color, fg=text_color, command=reload_ui_all).pack()

    refresh_ui = Button(aux_controls_frame, text='Refresh Plan Items',
                    anchor='w', font=(font, options_button_text_size),
                    bg=bg_color, fg=text_color, command=refresh_live_ui).pack()

    add_global_cues_button = Button(aux_controls_frame, text='Add Global Cue',
                    anchor='w', font=(font, options_button_text_size),
                    bg=bg_color, fg=text_color, command=add_global_cue).pack()

    load_adjacent_plan_button = Button(aux_controls_frame, text='Load Adjacent Plan',
                                       anchor='w', font=(font, options_button_text_size),
                                       bg=bg_color, fg=text_color, command=load_adjacent_plan).pack()


    # kipro stuff below
    if display_kipros:
        kipro_icons = []
        kipro_storage_remaining_bars = []
        # Create icons for kipro statuses, color them accordingly. Does not repeat.
        for kipro_index in kipro_data:
            if kipro_data[kipro_index]['name'] == 'ALL':
                pass
            else:
                kipro_name = kipro_data[kipro_index]['name']
                kipro_icons.append(Button(aux_controls_frame, text=kipro_name, font=(font, other_text_size),
                                         fg=text_color, height=2, relief=FLAT,
                                          command=lambda kipro_index = kipro_index:(
                                          kipro.toggle_start_stop(ip=kipro_data[kipro_index]['ip'],
                                                               name=kipro_data[kipro_index]['name'],
                                                               include_date=True), update_kipro_icons(delay=True))))

                kipro_status = kipro.get_status(ip=kipro_data[kipro_index]['ip'])
                # if idle, turn idle color
                if kipro_status == '1':
                    logging.debug('%s is idle, coloring icon', kipro_name)
                    kipro_icons[kipro_index-1].configure(bg=kipro_idle_color)
                # if recording, turn recording color
                if kipro_status == '2':
                    logging.debug('%s is recording, coloring icon', kipro_name)
                    kipro_icons[kipro_index-1].configure(bg=live_color)
                # if error, turn error color
                if kipro_status == '17':
                    logging.error('ERROR ON KIPRO %s', kipro_name)
                    kipro_icons[kipro_index-1].configure(bg=kipro_error_color)

                kipro_storage_remaining = int(kipro.get_remaining_storage(ip=kipro_data[kipro_index]['ip']))
                kipro_storage_remaining_bars.append(ttk.Progressbar(aux_controls_frame, length=110, mode='determinate', maximum=100))
                kipro_storage_remaining_bars[kipro_index-1].configure(value=kipro_storage_remaining)

        for iteration, kipro_icon in enumerate(kipro_icons):
            kipro_icons[iteration].pack()
            kipro_storage_remaining_bars[iteration].pack()
            Label(aux_controls_frame, bg=bg_color, font=(font, 1)).pack(fill='x')

        # update kipro labels based on status periodically. Interval is set in settings
        def interval_update_kipro_icons(enabled):
            if enabled:
                for kipro_index in kipro_data:
                    if not kipro_data[kipro_index]['name'] == 'ALL':
                        kipro_status = kipro.get_status(ip=kipro_data[kipro_index]['ip'])
                        # if idle, turn idle color
                        if kipro_status == '1':
                            kipro_icons[kipro_index - 1].configure(bg=kipro_idle_color)
                        # if recording, turn recording color
                        if kipro_status == '2':
                            kipro_icons[kipro_index - 1].configure(bg=live_color)
                        # if error, turn error color
                        if kipro_status == '17':
                            kipro_icons[kipro_index - 1].configure(bg=kipro_error_color)
                        if kipro_status == '18':
                            kipro_icons[kipro_index - 1].configure(bg=kipro_unable_to_commmunicate_color)

                        kipro_storage_remaining = int(kipro.get_remaining_storage(ip=kipro_data[kipro_index]['ip']))
                        kipro_storage_remaining_bars[kipro_index-1].configure(value=kipro_storage_remaining)
                kipro_icons[0].after(kipro_update_interval, lambda: interval_update_kipro_icons(enabled=interval_update_kipros))
        interval_update_kipro_icons(enabled=interval_update_kipros)

        # update icon color based on recording status
        def update_kipro_icons(delay):
            # Sleep if enabled, used when manually starting/stopping kipro from main ui. If disabled, sometimes kipro
            # won't start fast enough to update ui
            if delay:
                time.sleep(0.2)
            for kipro_index in kipro_data:
                if not kipro_data[kipro_index]['name'] == 'ALL':
                    kipro_status = kipro.get_status(ip=kipro_data[kipro_index]['ip'])
                    # if idle, turn idle color
                    if kipro_status == '1':
                        logging.debug('%s is idle, coloring icon', kipro_name)
                        kipro_icons[kipro_index - 1].configure(bg=kipro_idle_color)
                    # if recording, turn recording color
                    if kipro_status == '2':
                        logging.debug('%s is recording, coloring icon', kipro_name)
                        kipro_icons[kipro_index - 1].configure(bg=live_color)
                    # if recording error, turn error color
                    if kipro_status == '17':
                        logging.error('ERROR ON KIPRO %s', kipro_name)
                        kipro_icons[kipro_index - 1].configure(bg=kipro_error_color)
                    if kipro_status == '18':
                        kipro_icons[kipro_index - 1].configure(bg=kipro_unable_to_commmunicate_color)

    # create frame to hold controls at bottom
    service_controls_frame = Frame(plan_window, bg=bg_color, bd=2)

    # add global cue buttons
    #Check if plan app cue note exists, create placeholder if not
    if pco_plan_update.check_if_plan_app_cue_exists(service_type=plan_main_info['folder_id'],
                                                    plan=plan_main_info['plan_id']):
        plan_note_id = pco_plan_update.get_plan_app_cue_note_id(service_type=plan_main_info['folder_id'],
                                                                plan=plan_main_info['plan_id'])[0]
    else:
        pco_plan_update.create_plan_app_cue(service_type=plan_main_info['folder_id'],
                                            plan=plan_main_info['plan_id'], note_content='temp note content')
        plan_note_id = pco_plan_update.get_plan_app_cue_note_id(service_type=plan_main_info['folder_id'], plan=plan_main_info['plan_id'])

    logging.debug('plan_note_id is %s', plan_note_id)
    # pass app cue note id to get_plan_note_content, returns a dict
    global_cues = pco_plan_update.get_plan_note_content(service_type=plan_main_info['folder_id'],
                                                        plan=plan_main_info['plan_id'], note_id=plan_note_id)

    # feed me a single item
    # cue_coder.cue_decoder only takes a iterable, we first have to put the single item in a list
    def cue_global_cue(cue):
        cue_list = []
        cue_list.append(cue)
        cue_coder.cue_decoder(cuedict=cue_list)

    global_cues_frame = Frame(service_controls_frame, bg=bg_color, bd=2)
    global_cue_buttons = []
    if type(global_cues) == dict:
        for iteration, cue in enumerate(global_cues):
            name = cue_coder.cue_verbose_decoder(cuedict=global_cues)[iteration]
            logging.debug('Verbose name of global cue button is %s', name)
            global_cue_buttons.append(Button(global_cues_frame,
                                      text=name, bg=bg_color, fg=text_color, font=(font, global_cue_font_size),
                                             command=lambda iteration = iteration: cue_global_cue(global_cues[str(iteration+1)])))

    for iteration, button in enumerate(global_cue_buttons):
        button.grid(row=0, column=iteration)

    next_previous_frame = Frame(service_controls_frame, bg=bg_color)
    logging.debug('Adding previous (no actions) button.')
    btn_previous_without_actions = Button(next_previous_frame,
                          text='PREVIOUS (no actions)',
                          bg=accent_color_1,
                          fg=accent_text_color,
                          font=(accent_text_font, producer_note_text_size),
                          command=lambda: previous(cue_items=False)).grid(row=1, column=0)

    logging.debug('adding previous button')
    btn_previous = Button(next_previous_frame,
                          text='PREVIOUS',
                          bg=accent_color_1,
                          fg=accent_text_color,
                          font=(accent_text_font, accent_text_size),
                          command=lambda: previous(cue_items=True)).grid(row=1, column=1)

    logging.debug('Adding next button')
    btn_next = Button(next_previous_frame,
                      text='NEXT',
                      bg=accent_color_1,
                      fg=accent_text_color,
                      font=(accent_text_font, accent_text_size),
                      command=lambda: next(cue_items=True)).grid(row=1, column=2)

    logging.debug('Adding next (no actions) button.')
    btn_next_without_actions = Button(next_previous_frame,
                          text='NEXT (no actions)',
                          bg=accent_color_1,
                          fg=accent_text_color,
                          font=(accent_text_font, producer_note_text_size),
                          command=lambda: next(cue_items=False)).grid(row=1, column=3)

    # main plan window
    clock_frame.grid(sticky='w', row=0, column=0)
    service_plan_frame.grid(row=1, column=0)
    aux_controls_frame.grid(sticky='w', row=1, column=2)

    # bottom bit
    service_controls_frame.grid(row=2, column=0)
    global_cues_frame.grid(row=0, column=0)
    # spacer between global cues and next/previous
    Frame(service_controls_frame, bg=bg_color, height=10).grid(row=1, column=0)
    next_previous_frame.grid(row=2, column=0)

    # loads initial plan
    refresh_live_ui()



