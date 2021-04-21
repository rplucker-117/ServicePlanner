import requests
from tkinter import *
import json
from settings import *
import time
import pprint
import logging
import datetime
from pvp import pvp
from pco_plan import pco_plan
# from main import reload_ui
from tkinter import ttk

# from main import items_master

cues = {}
def cue_creator_window(plan_items, item_index, service_type, plan_id):
    def add_cg3_cue_clicked():
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
            cues.update({len(cues) + 1: {
                'device': 'CG3',
                'playlist_index': playlist_index,
                'cue_index': cue_index,
                'cue_name': cue_name}
            })
            update_cues_display(cue_dict=cues, item_index=item_index)

    def add_cg4_cue_clicked():
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
            cues.update({len(cues) + 1: {
                'device': 'CG4',
                'playlist_index': playlist_index,
                'cue_index': cue_index,
                'cue_name': cue_name}
            })
            update_cues_display(cue_dict=cues, item_index=item_index)

    def add_pause_cue_clicked():
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
            cues.update({len(cues) + 1: {
                'device': 'Pause',
                'time': seconds
            }})
            add_pause_window.destroy()
            update_cues_display(cue_dict=cues, item_index=item_index)

    def add_rosstalk_cue_clicked():
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
                cues.update({len(cues) + 1: {
                    'device': 'Rosstalk',
                    'type': 'CC',
                    'bank': bank,
                    'CC': CC
                }})
                update_cues_display(cue_dict=cues, item_index=item_index)

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
                update_cues_display(cue_dict=cues, item_index=item_index)

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
                update_cues_display(cue_dict=cues, item_index=item_index)

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
        buttons.append(key_cut_btn)
        buttons.append(key_auto_btn)

        for iteration, button in enumerate(buttons):
            button.grid(row=iteration + 2, column=0)

    def add_reminder_cue_clicked():
        # creates a new window for adding a reminder with minutes, seconds, reminder text, and okay.
        logging.debug('add reminder button clicked')
        add_reminder_window = Tk()
        add_reminder_window.config(bg=bg_color)

        def okay_pressed():
            minutes = minutes_entry.get()
            seconds = seconds_entry.get()
            reminder = reminder_entry.get()

            cues.update({len(cues)+ 1: {
                'device': 'Reminder',
                'minutes': int(minutes),
                'seconds': int(seconds),
                'reminder': str(reminder)
            }})

            logging.debug('Okay button pressed on add_reminder_window. Minutes: %s, '
                          'Seconds: %s, Str: %s', minutes, seconds, reminder)
            add_reminder_window.destroy()
            update_cues_display(cue_dict=cues, item_index = item_index)

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

    def add_kipro_cue_clicked():
        # creates new window for starting/stopping kipros. Either all or single.
        add_kipro_cue_window = Tk()
        add_kipro_cue_window.config(bg=bg_color)

        def okay_pressed():
            # when okay button in add_kipro_cue_window is pressed. start is true when command is to start recording,
            # start is false when command is to stop. 0 is to start ALL, any other int is to start any other
            # individual ones after that.

            start = start_stop_selected.get()
            kipro = kipro_selected.get()
            logging.debug('okay_button pressed in add_kipro_cue_window. start = %s, kipro = %s', start, kipro)
            cues.update({len(cues) + 1:{
                'device': 'Kipro',
                'start': start,
                'kipro': kipro
            }})
            add_kipro_cue_window.destroy()
            update_cues_display(cue_dict=cues, item_index=item_index)


        start_stop_frame = Frame(add_kipro_cue_window)
        start_stop_frame.config(bg=bg_color)
        start_stop_frame.grid(row=0, column=0)

        start_stop_selected = BooleanVar(start_stop_frame, value=0)

        # add start/stop buttons. Changes value of start_stop_selected variable above.
        # TRUE means start, FALSE means stop.
        start_selected = Radiobutton(start_stop_frame,
                                     bg=bg_color,
                                     fg=text_color,
                                     text='Start',
                                     font=(font, current_cues_text_size),
                                     selectcolor=bg_color,
                                     padx=20,
                                     variable=start_stop_selected,
                                     value=True,
                                     command=lambda: logging.debug('Start_selected button pressed')
                                     ).pack()

        stop_selected = Radiobutton(start_stop_frame,
                                     bg=bg_color,
                                     fg=text_color,
                                     text='Stop',
                                     font=(font, current_cues_text_size),
                                     selectcolor=bg_color,
                                     padx=20,
                                     variable=start_stop_selected,
                                     value=False,
                                     command=lambda: logging.debug('Stop_selected button pressed.')
                                     ).pack()

        kipro_select_frame = Frame(add_kipro_cue_window)
        kipro_select_frame.config(bg=bg_color)
        kipro_select_frame.grid(row=0, column=1)

        kipro_selected = IntVar(kipro_select_frame, value=0)

        # create group of radiobuttons from kipro_data in settings.py and add them to list
        kipros = []
        for kipro in kipro_data:
            kipros.append(Radiobutton(kipro_select_frame,
                                      bg=bg_color,
                                      fg=text_color,
                                      text=kipro_data[kipro]['name'],
                                      font=(font, current_cues_text_size),
                                      selectcolor=bg_color,
                                      padx=20,
                                      variable=kipro_selected,
                                      value=kipro,
                                      command=lambda: logging.debug('kipro button pressed: %s', kipro_data[kipro]['name'])))
        for radiobutton in kipros:
            radiobutton.pack()

        okay_button = Button(add_kipro_cue_window,
                             text='okay',
                             bg=bg_color,
                             fg=text_color,
                             font=(font, plan_text_size),
                             command=okay_pressed).grid(row=1, column=0)

    # def add_resi_cue_clicked():
    #     add_resi_cue_window = Tk()
    #     add_resi_cue_window.config(bg=bg_color)
    #
    #     commands={
    #         1: {
    #             'name': 'Play',
    #             'command': 'CC play'
    #         },
    #         2: {
    #             'name': 'Pause',
    #             'command': 'CC pause'
    #         },
    #         3: {
    #             'name': 'Play and fade from black',
    #             'command': 'CC PAFFB'
    #         },
    #         4: {
    #             'name': 'Fade to black and pause',
    #             'command': 'CC FTBAP'
    #         },
    #         5: {
    #             'name': 'Fade from black (no change in playing state)',
    #             'command': 'CC FFB'
    #         },
    #         6: {
    #             'name': 'Fade to black (no change in playing state)',
    #             'command': 'CC FTB'
    #         }
    #     }
    #
    #     resi_buttons = []
    #     for iteration in commands:
    #         resi_buttons.append(Button(add_resi_cue_window,
    #                                    text=commands[iteration]['name'],
    #                                    bg=bg_color,
    #                                    fg=text_color,
    #                                    font=(font, current_cues_text_size),
    #                                    command=lambda: button_pressed(iteration)))
    #     for button in resi_buttons:
    #         button.pack()




    # Create root window and withdraw it so we can destroy main cue creator window
    root = Tk()
    root.withdraw()

    # Create main cue creator window
    cue_creator = Tk()
    cue_creator.configure(bg=bg_color)

    # create frame for text displaying the cues to be added
    current_cues_frame = Frame(cue_creator, bg=bg_color, width=600, height=300)
    current_cues_frame.grid(row=0, column=0)
    current_cues_frame.grid_propagate(0)

    # create frame for add cue type buttons
    cue_type_buttons_frame = Frame(cue_creator, bg=bg_color)
    cue_type_buttons_frame.grid(row=0, column=2)

    # create frame for bottom buttons (okay, cancel, add quick cue, etc)
    bottom_buttons_frame = Frame(cue_creator, bg=bg_color)
    bottom_buttons_frame.grid(row=1, column=0)

    # label for displaying the cues that will be added
    current_cues_label = Label(current_cues_frame, bg=bg_color, fg=text_color, font=(font, current_cues_text_size),
                               anchor='w', justify='left', text=f"Cues to be added to "
                                                                f"{plan_items[item_index]['item_title']}: \n\n")
    current_cues_label.grid(row=1, column=0)

    # this function updates the current_cues_label after a cue has been selected. Visual only
    def update_cues_display(cue_dict, item_index):
        def update_cues():
            current_cues_label.config(text=f"{current_cues_label.cget('text')}\n{text_to_update}")
            final_cue_in_list = len(cue_dict) + 1
        if cue_dict[len(cue_dict)]['device'] in ('CG3', 'CG4'):
            text_to_update = f"({cue_dict[len(cue_dict)]['device']}):   Cue {cue_dict[len(cue_dict)]['cue_name']}" \
                             f" (playlist {int(cue_dict[len(cue_dict)]['playlist_index']) + 1}, cue {int(cue_dict[len(cue_dict)]['cue_index']) + 1})"
            update_cues()
        if cue_dict[len(cue_dict)]['device'] == 'Pause':
            text_to_update = f"Pause:   {cue_dict[len(cue_dict)]['time']} seconds."
            update_cues()
        if cue_dict[len(cue_dict)]['device'] == 'Reminder':
            text_to_update = f"Reminder:    [{cue_dict[len(cue_dict)]['reminder']}]: " \
                             f"after {cue_dict[len(cue_dict)]['minutes']} minutes, " \
                             f"{cue_dict[len(cue_dict)]['seconds']} seconds."
        if cue_dict[len(cue_dict)]['device'] == 'Kipro':
            if cue_dict[len(cue_dict)]['start'] == True:
                mode = 'Start'
            else:
                mode = 'Stop'
            text_to_update = f"Kipro:   {mode} {kipro_data[cue_dict[len(cue_dict)]['kipro']]['name']}"
            update_cues()
        if cue_dict[len(cue_dict)]['device'] == 'Rosstalk':
            if cue_dict[len(cue_dict)]['type'] == 'CC':
                text_to_update = f"Rosstalk:    CC {cue_dict[len(cue_dict)]['bank']}:{cue_dict[len(cue_dict)]['CC']}"
                update_cues()
            if cue_dict[len(cue_dict)]['type'] == 'KEYCUT':
                text_to_update = f"Rosstalk:    KEYCUT {cue_dict[len(cue_dict)]['bus']}, KEY {cue_dict[len(cue_dict)]['key']}"
                update_cues()
            if cue_dict[len(cue_dict)]['type'] == 'KEYAUTO':
                text_to_update = f"Rosstalk:    KEYAUTO {cue_dict[len(cue_dict)]['bus']}, KEY {cue_dict[len(cue_dict)]['key']}"
                update_cues()

    add_cg3_cue = Button(cue_type_buttons_frame,
                         text='Add CG3 PVP Cue',
                         font=(font, plan_text_size),
                         bg=bg_color,
                         fg=text_color,
                         command=add_cg3_cue_clicked)
    add_cg3_cue.pack()

    add_cg4_cue = Button(cue_type_buttons_frame,
                         text='Add CG4 PVP Cue',
                         font=(font, plan_text_size),
                         bg=bg_color,
                         fg=text_color,
                         command=add_cg4_cue_clicked)
    add_cg4_cue.pack()

    add_rosstalk_cue = Button(cue_type_buttons_frame,
                              text='Add Rosstalk Cue',
                              font=(font, plan_text_size),
                              bg=bg_color,
                              fg=text_color,
                              command=add_rosstalk_cue_clicked)
    add_rosstalk_cue.pack()

    add_kipro_cue = Button(cue_type_buttons_frame,
                           text='Add KiPro Cue',
                           font=(font, plan_text_size),
                           bg=bg_color,
                           fg=text_color,
                           command=add_kipro_cue_clicked)
    add_kipro_cue.pack()


    add_resi_cue = Button(cue_type_buttons_frame,
                          text='Add Resi Cue',
                          font=(font, plan_text_size),
                          bg=bg_color,
                          fg=text_color)
    add_resi_cue.pack()

    add_pause = Button(cue_type_buttons_frame,
                       text='Add Pause',
                       font=(font, plan_text_size),
                       bg=bg_color,
                       fg=text_color,
                       command=add_pause_cue_clicked)
    add_pause.pack()

    add_reminder = Button(cue_type_buttons_frame,
                          text='Add Reminder',
                          font=(font, plan_text_size),
                          bg=bg_color,
                          fg=text_color,
                          command=add_reminder_cue_clicked)
    add_reminder.pack()

    # closes the cue_creator window, runs the finished() function and passes finished cue dictionary to it
    add_cues_button = Button(bottom_buttons_frame,
                             text='Add Cues to Planning Center',
                             font=(font, plan_text_size),
                             bg=bg_color,
                             fg=text_color,
                             command=lambda: (finished(cue_dict=cues)))
    add_cues_button.grid(row=0, column=0)

    # nuke everything
    cancel_button = Button(bottom_buttons_frame,
                           text='Cancel',
                           font=(font, plan_text_size),
                           bg=bg_color,
                           fg=text_color,
                           command=cue_creator.destroy)
    cancel_button.grid(row=0, column=1)

    # runs when 'add cues' button has been clicked. Calls create and update app cue and pushes it live to pco plan.
    # Also destroys cue_creator window and clears cues dict when finished
    def finished(cue_dict):
        adding_cues_window = Tk()
        adding_cues_window.configure(bg=bg_color)
        adding_cues_window.geometry('500x150')

        status = Label(adding_cues_window,
                       bg=bg_color,
                       fg=text_color,
                       font=(font, other_text_size),
                       text='Adding selected cues to PCO..')
        status.pack(anchor='center')
        pco_plan.create_and_update_item_app_cue(service_type=service_type, plan=plan_id,
                                                item_id=plan_items[item_index]['item_id'],
                                                app_cue=json.dumps(cues))
        cues.clear()
        root.destroy()
        cue_creator.destroy()
        adding_cues_window.destroy()

    root.mainloop()
