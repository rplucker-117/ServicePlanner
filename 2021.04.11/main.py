def create_ui(plan_items):

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
            name = cue_coder.cue_verbose_decoder(cuelist=global_cues)[iteration]
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

