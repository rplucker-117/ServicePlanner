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

logging.debug('Starting initial api request')

# make initial request for service types, load into dictionary
try:
    top_request = requests.get('https://api.planningcenteronline.com/services/v2/service_types/', auth=(APP_ID, SECRET))
    toplevel_json = json.loads(top_request.text)
    logging.debug('Initial API request made successfully')
    try:
        error = toplevel_json['errors']
        logging.critical(
            'Connected to planning center, but 404 was returned. Check your api credentials. Halting program.')
        quit()
    except KeyError:
        pass
except:
    logging.critical(
        'Initial request returned an error. Check your network connection/api credentials. Halting program.')
    quit()

logging.debug('Creating ui...')
# create list of service folder type names
service_types = []
for service_type in range(len(toplevel_json['data'])):
    service_types.append(toplevel_json['data'][service_type]['attributes']['name'])

# start tk
root = Tk()
# hide root window, dont need it
root.withdraw()

# create button for each service type, assign index to each button, call service_type_select function
service_type_pick_window = Tk()
service_type_pick_window.title('Pick service folder')
service_type_pick_window.configure(bg=bg_color)

items_master = {}

plan_main_info = {
    'folder_id': None,
    'plan_id': None,
    'plan_index': None
}

logging.debug('Creating service folder list')
# create list with length of all
for service_type_index in range(len(service_types)):
    service_type_button = Button(service_type_pick_window, text=service_types[service_type_index],
                                 command=lambda service_type_index=service_type_index: select_service_folder_from_list(
                                     service_type_index),
                                 bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1, width=50, pady=3)
    service_type_button.pack()

# Select service type folder, return id from index, pass to service_select fun
def select_service_folder_from_list(value):
    logging.debug('Creating service folder window + buttons')
    global service_type_index
    global service_type_id
    service_type_index = value
    service_type_pick_window.destroy()
    service_type_id = toplevel_json['data'][service_type_index]['id']
    plan_main_info.update({'folder_id': service_type_id})
    select_service_from_list(service_type_id)
    logging.debug('service type id = %s', service_type_id)

# create widow to select service from
def select_service_from_list(service_type_id):
    logging.debug('Making api call to view total number of plans')
    # Make request to view total number of plans in the selected service type
    service_request = requests.get(
        f'https://api.planningcenteronline.com/services/v2/service_types/{service_type_id}/plans',
        auth=(APP_ID, SECRET))
    service_json = json.loads(service_request.text)

    logging.debug('Making api call to load list of all plans in service type')
    # Offset number of viewed plans to show only most recent ones, return dict with plans
    offset = service_json['meta'][
                 'total_count'] - 15  # <----- how many plans to view at once, starting from the most future one. Increase this number if you plan far in advance...
    service_request_with_offset = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                                               f'{service_type_id}/plans?filter=&offset={offset}',
                                               auth=(APP_ID, SECRET))
    global services_final  # for use in service_select function
    services_final = json.loads(service_request_with_offset.text)

    # create list with length of all , for use below for button width value
    service_name_lengths = []
    for service in range(len(services_final['data'])):
        service_name_lengths.append(len(services_final['data'][service]['attributes']['dates']))
    # sort service_name_lengths list
    service_name_lengths.sort()
    longest_service_name = service_name_lengths[-1]

    logging.debug('populating list of all services')
    # create + populate list for services
    services = []
    for service in range(len(services_final['data'])):
        services.append(services_final['data'][service]['attributes']['dates'])

    # create tk window with buttons to pick services
    global service_pick_window  # for use in service_select function
    service_pick_window = Tk()
    service_pick_window.configure(bg=bg_color)
    service_pick_window.title('Pick Service')

    logging.debug('Creating service buttons')
    # create service buttons
    for service_index in range(len(services)):
        service_button = Button(service_pick_window, text=services[service_index],
                                command=lambda service_index=service_index: service_selected(
                                    service_type_id=service_type_id,
                                    service_index=service_index),
                                bg=bg_color, fg=text_color, font=(font, other_text_size), bd=1,
                                width=longest_service_name, pady=3)
        service_button.pack()

def service_selected(service_type_id, service_index):
    #For use when reload_ui button is pressed.
    try:
        service_pick_window.destroy()
    except:
        logging.debug("service_pick_window doesn't exist! Continuing anyway...")
        pass


    plan_main_info.update({'plan_index': service_index})

    # id of service
    service_id = services_final['data'][service_index]['id']
    logging.debug('service_id = %s', service_id)

    plan_main_info.update({'plan_id': service_id})

    logging.debug('Making api call to get plan data including dates')
    # plan data including dates
    plan_request = requests.get(
        f'https://api.planningcenteronline.com/services/v2/service_types/{service_type_id}/plans/{service_id}',
        auth=(APP_ID, SECRET))
    plan_data = json.loads(plan_request.text)

    logging.debug('Making api call to get service items')
    plan_item_request = requests.get(
        f'https://api.planningcenteronline.com/services/v2/service_types/{service_type_id}/plans/{service_id}/items',
        auth=(APP_ID, SECRET))
    plan_items = json.loads(plan_item_request.text)



    # create dictionary to hold plan data because PCO doesn't give you all item data at once: you have to request data
    # from each plan item individually in a separate api call. it first puts the item title and item type
    # into a nested dictionary and creates a placeholder for other item types.

    for iteration, data in enumerate(plan_items['data']):
        logging.debug('Creating dictionary entry for item %s', data['attributes']['title'])
        items_master.update({
            iteration: {
                'item_title': data['attributes']['title'],
                'item_type': data['attributes']['item_type'],
                'person': None,
                'person_notes_item_id': None,
                'producer_notes': None,
                'producer_notes_item_id': None,
                'app_cues': None,
                'app_cues_item_id': None,
                'app_cues_verbose': None,
                'app_cues_note_category_id': app_cue_note_category_id,
                'item_id': data['id'],
                'item_length': data['attributes']['length'],
            }
        })

    # Now after dictionary item titles/types are entered, we make an api call for each item, and load its data into
    # each respective dictionary, starting by putting all item note ids into a list, and making the call for each
    # item in that list.

    plan_loading_window = Tk()
    plan_loading_window.geometry('700x100')
    loading_plan_label = Label(plan_loading_window, text='Loading plan, please wait.',
                               bg=bg_color, fg=text_color, font=(font, current_cues_text_size))
    loading_plan_label.pack()
    progress_bar = ttk.Progressbar(plan_loading_window, length=600, mode='determinate', maximum=len(plan_items['data']))

    item_note_ids = []
    for item_index in range(len(plan_items['data'])):
        item_note_ids.append(plan_items['data'][item_index]['id'])

    for iteration, item_note in enumerate(item_note_ids):
        logging.debug('making api call for item notes for item id: %s', item_note)
        item_json = json.loads(requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                                            f'{service_type_id}/plans/{service_id}/items/{item_note}/item_notes',
                                            auth=(APP_ID, SECRET)).text)
        plan_loading_window.configure(bg=bg_color)
        progress_bar.step(1)
        progress_bar.pack()
        plan_loading_window.update_idletasks()

        item_ids = pco_plan_update.get_item_note_id(service_type=service_type_id, plan=service_id, item_id=item_note)

        for data_iteration, item_tag in enumerate(item_json['data']):
            if item_tag['attributes']['category_name'] == 'Person':
                items_master[iteration].update({'person_notes_item_id': item_ids['Person']})
                items_master[iteration].update({'person': item_tag['attributes']['content']})
            if item_tag['attributes']['category_name'] == 'Producer Notes':
                items_master[iteration].update({'producer_notes_item_id': item_ids['Producer Notes']})
                items_master[iteration].update({'producer_notes': item_tag['attributes']['content']})
            if item_tag['attributes']['category_name'] == 'App Cues':
                items_master[iteration].update({'app_cues_item_id': item_ids['App Cues']})
                items_master[iteration].update({'app_cues': json.loads(item_tag['attributes']['content'])})

    plan_loading_window.destroy()

    # Convert all app cue dicts to simple human-readable text, add to app_cues
    # verbose dictionary entry for respective item in items_master under service_selected function
    # conversion from dictionary to human-readable text is done by cue_coder()
    for iteration, item in enumerate(items_master):
        cue_list = cue_coder.cue_verbose_decoder(cuedict=items_master[iteration]['app_cues'])
        cue_to_append = str()
        if not cue_list == None:
            for cue in cue_list:
                cue_to_append = (cue_to_append + f"{cue}\n")
            items_master[iteration]['app_cues_verbose'] = cue_to_append


    create_ui(plan_items=items_master)

# pulls all data down from pco again. Only used in setup, never in live service. Takes 15+ seconds
def reload_ui_all():
    plan_window.destroy()
    service_selected(service_type_id=plan_main_info['folder_id'], service_index=plan_main_info['plan_index'])

# looks at which item is live, updates ui accordingly. Does not pull item details down again, unlike reload_ui_all()
def create_ui(plan_items):
    logging.debug('Creating plan ui')

    global plan_window
    plan_window = Tk()
    plan_window.configure(bg=bg_color)

    logging.debug('starting clock')
    clock_frame = Frame(plan_window, bg=bg_color)
    time_label = Label(clock_frame,
                       fg=clock_text_color,
                       bg=bg_color,
                       font=(clock_text_font, clock_text_size))
    time_label.grid(row=0, column=0)

    def clock():
        time_string = time.strftime('%H:%M:%S %p')
        time_label.config(text=time_string)
        time_label.after(1000, clock)

    clock()
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

    plan_item_frames = []
    #Create frame for each plan item. Height is determined by number of lines in app_cues_verbose.
    for iteration, item in enumerate(plan_items):
        line_height=40
        # count number of lines in app_cues_verbose, use it as item height.
        if not items_master[iteration]['app_cues_verbose'] == None:
            line_height = plan_items[iteration]['app_cues_verbose'].count('\n')*10
            if line_height < 40:
                line_height = 40
            if line_height > 130:
                line_height = 130
        logging.debug('Current line height for item %s is %s.', plan_items[iteration]['item_title'], line_height)
        plan_item_frames.append(Frame(service_plan_frame, bg=ui_debug_color, width=1200, height=line_height))
        if plan_items[iteration]['item_type'] == 'header':
            plan_item_frames[iteration].configure(bg=header_color, height=20)
        plan_item_frames[iteration].grid(row=iteration, column=0, sticky='w')
        plan_item_frames[iteration].grid_propagate(0)

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

    # kipro stuff below

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

                    kipro_storage_remaining = int(kipro.get_remaining_storage(ip=kipro_data[kipro_index]['ip']))
                    kipro_storage_remaining_bars[kipro_index-1].configure(value=kipro_storage_remaining)
            kipro_icons[0].after(kipro_update_interval, lambda: interval_update_kipro_icons(enabled=interval_update_kipros))
    interval_update_kipro_icons(enabled=interval_update_kipros)

    # update icon color based on recording status
    def update_kipro_icons(delay):
        # Sleep if enabled, used when manually starting/stopping kipro from main ui. If disabled, sometimes kipro
        # won't start fast enough to update ui
        if delay:
            time.sleep(0.1)
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
                # if error, turn error color
                if kipro_status == '17':
                    logging.error('ERROR ON KIPRO %s', kipro_name)
                    kipro_icons[kipro_index - 1].configure(bg=kipro_error_color)

    # create frame to hold controls at bottom
    service_controls_frame = Frame(plan_window, bg=bg_color, bd=2)

    # add global cue buttons
    plan_note_id = pco_plan_update.get_plan_app_cue_note_id(service_type=plan_main_info['folder_id'],
                                                            plan=plan_main_info['plan_id'])[0]
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
    aux_controls_frame.grid(sticky='e', row=1, column=1)

    # bottom bit
    service_controls_frame.grid(row=2, column=0)
    global_cues_frame.grid(row=0, column=0)
    # spacer between global cues and next/previous
    Frame(service_controls_frame, bg=bg_color, height=10).grid(row=1, column=0)
    next_previous_frame.grid(row=2, column=0)

    # loads initial plan
    refresh_live_ui()


root.mainloop()
