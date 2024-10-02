from configs.settings import *
import json
import os
from tkinter import *
from pprint import pprint
from os import path
from logzero import logger
from typing import List
from cue_creator import CueCreator
from cue_handler import CueHandler
from pco_plan import PcoPlan
from flask import Flask, request
from general_networking import is_local_port_in_use
from threading import Thread


class GlobalCues:
    """
    All functionality for Global cues, including ui. This can be run independently of the main app.

    Cues are stored in banks of 8, with 32 cues per bank in [[{'name': 'cue 1', 'cues': []}, {'name': 'cue 2', 'cues': []}, {'name': None, 'cues': []} ]]
    format.
    """

    def __init__(self):

        self.folder_path = os.path.dirname(__file__)

        test = path.join(self.folder_path, 'configs', 'global_cues.json')

        # if global cues file does not exist, create an empty one
        if not path.exists(path.join(self.folder_path, 'configs', 'global_cues.json')):
            self._create_empty_global_cues_file()

        with open(os.path.join(self.folder_path, 'configs', 'devices.json'), 'r') as f:
            self.devices: List[dict] = json.loads(f.read())

        self.cue_handler = CueHandler(devices=self.devices)

        self.global_cues: List[List[dict]] = self.read_global_cues()
        self._correct_old_pvp_cues()

        self.root: Tk = Tk()

        self.bank_frame: Frame = Frame(self.root)
        self.cues_frame: Frame = Frame(self.root)

        self.bank_buttons: List[Button] = []
        self.cue_buttons: List[Button] = []

        self.currently_selected_bank: int = 0

        self.edit_mode: bool = False

        self._start_self_contained_webserver()


    def read_global_cues(self) -> list:
        """
        Read global cues from file & return it as a python object
        :return: global cues read from file
        """
        with open(path.join(self.folder_path, 'configs', 'global_cues.json')) as f:
            return json.loads(f.read())

    def _correct_old_pvp_cues(self):
        has_been_changed: list = [False]
        for bank in self.global_cues:
            for global_cue in bank:
                for cue in global_cue['cues']:
                    device = self.cue_handler.get_device_from_uuid(cue['uuid'])
                    if device['type'] == 'pvp':
                        if 'cue_name' in cue.keys():
                            logger.info('Found old PVP cue in global cue, fixing...')
                            has_been_changed[0] = True
                            cue.pop('cue_name')
                            cue['cue_type'] = 'cue_cue'

        if has_been_changed[0]:
            with open(path.join(self.folder_path, 'configs', 'global_cues.json'), 'w') as f:
                f.write(json.dumps(self.global_cues))

    def open_global_cues_window(self) -> None:
        """
        Opens the main global cues window
        :return: None
        """
        self.root.configure(bg=bg_color)
        self.root.geometry('1600x900')
        self.root.title('Global Cues Shotbox')
        self.root.grid_columnconfigure(0, weight=1)

        self.bank_frame.configure(bg=bg_color)
        self.bank_frame.grid(row=0, column=0, pady=20)

        self.cues_frame.configure(bg=bg_color)
        self.cues_frame.grid(row=1, column=0)

        # build bank buttons
        for i, bank in enumerate(self.global_cues):
            new_button = Button(self.bank_frame,
                                bg=bg_color,
                                width=11,
                                foreground=text_color,
                                font=(font, 20),
                                text=f'Bank {i + 1}',
                                command=lambda i=i: self._switch_to_bank(bank=i))
            new_button.grid(row=0, column=i, padx=4, pady=10)
            self.bank_buttons.append(new_button)

        # build cue buttons
        row_counter = 0
        column_counter = 0

        for i in range(32):
            new_button = Button(self.cues_frame,
                                bg=bg_color,
                                width=12,
                                height=5,
                                foreground=text_color,
                                font=(font, 17),
                                wraplength=180,
                                command=lambda i=i: self._cue_button_clicked(index=i))

            # Starting a new column
            if column_counter >= 8:
                row_counter += 1
                column_counter = 0

            new_button.grid(row=row_counter, column=column_counter, padx=5, pady=10)
            self.cue_buttons.append(new_button)

            column_counter += 1

        self._switch_to_bank(0)

        Button(self.root, bg=bg_color, foreground=text_color, font=(font, 14), text='Edit Mode',
               command=self._toggle_edit_mode).grid(row=2, column=0, sticky='w', padx=25, pady=20)

        self.root.mainloop()

    def _create_empty_global_cues_file(self) -> None:
        logger.info('Creating empty global cues file')

        global_cues = []
        for x in range(8):
            global_cues.append([])
            for i in range(32):
                global_cues[x].append({
                    'name': '',
                    'cues': []
                })

        with open(path.join(self.folder_path, 'configs', 'global_cues.json'), 'w') as f:
            f.write(json.dumps(global_cues))

    def _cue_button_clicked(self, index: int) -> None:
        """
        Activate cues associated with a cue button
        :param index: index of the cue within the selected bank
        :return: None
        """

        logger.debug(f'Cue button clicked: {self.currently_selected_bank}:{index}')

        if self.edit_mode:
            self._toggle_edit_mode()
            self._edit_cue(bank=self.currently_selected_bank, cue_index=index)
        else:
            Thread(target=lambda: self.cue_handler.activate_cues(cuelist=self.global_cues[self.currently_selected_bank][index]['cues'])).start()

    def _switch_to_bank(self, bank: int) -> None:
        """
        Changes functionality of cue buttons to match specific bank
        :param bank: bank desired to swap to
        :return: None
        """

        logger.debug(f'Swapping to bank {bank}')

        self.currently_selected_bank = bank

        # Change name of cue buttons to match bank
        for i, button in enumerate(self.cue_buttons):
            button.configure(text=self.global_cues[self.currently_selected_bank][i]['name'])

        # Color currently selected bank button
        for i, button in enumerate(self.bank_buttons):
            if i == self.currently_selected_bank:
                button.configure(bg='#4a4a4a')
            else:
                button.configure(bg=bg_color)

        self._color_cue_buttons()

    def _toggle_edit_mode(self) -> None:
        """
        Toggle functionality of buttons from cue mode to edit mode
        :return: None
        """

        # flip edit mode bool
        self.edit_mode = not self.edit_mode

        if self.edit_mode:
            for button in self.cue_buttons:
                button.configure(bg='#53804e')
        else:
            self._color_cue_buttons()

    def _color_cue_buttons(self) -> None:
        """
        Colors cue buttons accordingly. Dark grey if there's no cues on them, light grey if they contain cues, red if errored.
        :return: None
        """
        for cue, button in zip(self.global_cues[self.currently_selected_bank], self.cue_buttons):
            cue_data = cue['cues']
            if cue_data != []:
                button.configure(bg='#4a4a4a')
            else:
                button.configure(bg=bg_color)

        def check_if_cues_online() -> None:
            """
            Checks to see if all cues within each cue button are valid. Colors red if not.
            :return: None
            """

            for i, global_cue in enumerate(self.global_cues[self.currently_selected_bank]):
                cuelist_valid = self.cue_handler.cues_are_valid(cuelist=global_cue['cues'])

                for cue in cuelist_valid:
                    if False in cue.keys():
                        self.cue_buttons[i].configure(bg='#a34444')

        Thread(target=check_if_cues_online).start()

    def _edit_cue(self, bank: int, cue_index: int):
        class FakeUI:
            def __init__(self):
                self.fake: None
                self.pco_plan = PcoPlan()

        class FakeMain:
            def __init__(self):
                self.service_type_id = 0
                self.service_id = 0

        cue_creator = CueCreator(startup=FakeMain(), ui=FakeUI(), devices=self.devices)
        cue_creator.edit_global_cue(global_cues=self.global_cues, cue_bank=bank, cue_index=cue_index,
                                    global_cue_shotbox_init=self)

    def _reload(self):
        self.global_cues = self.read_global_cues()
        self._switch_to_bank(self.currently_selected_bank)

    def _start_self_contained_webserver(self) -> None:
        """
        Start a webserver that takes post requests at http://localhost:80/activate_global_cue?&bank=2&cue_index=3
        :return: None
        """

        webserver_port = 7777

        if not is_local_port_in_use(webserver_port):
            logger.debug('Starting global cues webserver')
            app = Flask(__name__)

            @app.route('/activate_global_cue', methods=['POST'])
            def activate():
                bank: int = int(request.args.get('bank')) - 1
                cue_index: int = int(request.args.get('cue_index')) - 1

                logger.debug(f'Cueing global cues on bank {bank}, cue index {cue_index}')
                pprint(self.global_cues[bank][cue_index]['cues'])

                self.cue_handler.activate_cues(cuelist=self.global_cues[bank][cue_index]['cues'])

                return ''

            Thread(target=lambda: app.run('0.0.0.0', webserver_port)).start()

        else:
            logger.info('Primary application is using port 7777, not starting separate server for global cues')


if __name__ == '__main__':
    GlobalCues().open_global_cues_window()

