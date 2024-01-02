from tkinter import *
from cue_handler import CueHandler
from os import path
from configs.settings import *
import json
from logzero import logger
from typing import Union, Callable

class SoundCheckModeOptions:
    """
    Window for sound check options. Gives user ability to select devices to ignore cues on when sound check mode is active.
    """
    def __init__(self):
        self.sound_check_mode_window = Tk()

        devices_path = path.join(path.dirname(__file__), 'configs', 'devices.json')
        with open(devices_path, 'r') as f:
            self.devices = json.loads(f.read())

        self.ignored_devices: list[str] = []



    def _write_changes_to_disk(self) -> None:
        """
        Write serialized contents of ignored devices to disk.
        :return: None
        """

        with open(path.join(path.dirname(__file__), 'configs', 'sound_check_mode_devices.json'), 'w') as f:
            f.write(json.dumps(self.ignored_devices))

    def _okay(self, callback: Union[None, Callable]) -> None:
        """
        User wants to save changes and exit.
        :callback: callback function to execute
        :return: None
        """

        self._write_changes_to_disk()

        if callback is not None:
            callback()

        self.sound_check_mode_window.destroy()

    @staticmethod
    def read_sound_check_mode_devices() -> Union[list, None]:
        """
        Read and return deserialized contents of sound_check_mode_devices.json
        :return: None if file does not exist. Deserialized contents if it exists.
        """

        sound_check_mode_devices_file = path.join(path.dirname(__file__), 'configs', 'sound_check_mode_devices.json')

        if path.exists(sound_check_mode_devices_file):
            with open(sound_check_mode_devices_file, 'r') as f:
                return json.loads(f.read())
        else:
            logger.info(f'{__class__.__name__}.read_sound_check_mode_devices: sound_check_mode_devices.json does not exist.')
            return None

    def open_sound_check_mode_options_menu(self, callback: Callable = None) -> None:
        """
        Open soundcheck mode options window. This is the primary method that should be called externally.
        :param callback: Optional callback function to be called when "okay" button is pressed.
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.open_sound_check_mode_options_menu.__name__}: Opening sound check options menu')

        self.sound_check_mode_window.configure(bg=bg_color)

        Label(self.sound_check_mode_window, text='Select devices to ignore cues on when sound check mode is active.', bg=bg_color, fg=text_color, font=(font, other_text_size)).pack()

        # for use below in "ignored devices: x" text at bottom of window
        devices_ignored_selected_text_var = StringVar(self.sound_check_mode_window)
        devices_ignored_selected_text_var.set('Ignored Devices: 0')

        devices_frame = Frame(self.sound_check_mode_window, bg=bg_color)
        devices_frame.pack()

        existing_ignored_devices = self.read_sound_check_mode_devices()

        def checkbutton_changed(uuid: str):
            if uuid not in self.ignored_devices:
                self.ignored_devices.append(uuid)
            else:
                self.ignored_devices.remove(uuid)

            devices_ignored_selected_text_var.set(f'Ignored Devices: {len(self.ignored_devices)}')


        for i, device in enumerate(self.devices, start=1):
            if not device['uuid'] in (all_kipros_uuid, reminder_uuid, pause_uuid): # vars are in settings.py
                cb = Checkbutton(devices_frame, bg=bg_color, font=12, command=lambda device=device: checkbutton_changed(device['uuid']))
                cb.grid(row=i, column=0)
                Label(devices_frame, text=device['user_name'], bg=bg_color, fg=text_color, font=(font, other_text_size-1)).grid(row=i, column=1, sticky='w')

                #if the current device has previously been checked
                if existing_ignored_devices is not None and device['uuid'] in existing_ignored_devices:
                    cb.invoke()


        Label(self.sound_check_mode_window, textvariable=devices_ignored_selected_text_var, bg=bg_color, fg=text_color, font=(font, other_text_size-1)).pack(side=LEFT)

        Button(self.sound_check_mode_window, text='Okay', bg=bg_color, fg=text_color, font=(font, other_text_size), command=lambda: self._okay(callback)).pack(side=RIGHT)

        self.sound_check_mode_window.mainloop()

if __name__ == '__main__':
    SoundCheckModeOptions().open_sound_check_mode_options_menu()

