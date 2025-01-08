import os
import json
from logzero import logger
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from configs.settings import *
import uuid
import socket
from datetime import datetime
from shutil import copyfile
from midi import Midi
import tkinter.messagebox
from general_networking import is_mac_address_valid
from pprint import pprint


class DeviceEditor:
    def __init__(self):
        self.absolute_path = os.path.dirname(__file__)
        os.chdir(self.absolute_path)

        if os.path.exists(os.path.join('configs', 'devices.json')):
            logger.debug('DeviceEditor.__init__: devices.json exists. Reading...')
            with open(os.path.join('configs', 'devices.json'), 'r') as f:
                self.devices = json.loads(f.read())
        else:
            logger.info('DeviceEditor.__init__: devices.json does not exist. Setting to empty list, with reminder and pause.')
            self.devices = []

            # this program sees internal generic actions, such as pause and reminders, as "devices". Devices are
            # recognized by their uuid, so upon creation of a new file, we need to add them

            self.devices.append({
                'type': 'pause',
                'user_name': 'pause',
                'uuid': 'f0d73b84-60b1-4c1d-a49f-f3b11ea65d3f'
            })
            self.devices.append({
                'type': 'reminder',
                'user_name': 'reminder',
                'uuid': 'b652b57e-c426-4f83-87f3-a7c4026ec1f0'
            })
            self.devices.append({
                'type': 'kipro',
                'user_name': 'All Kipros',
                'uuid': '07af78bf-9149-4a12-80fc-0fa61abc0a5c'
            })
            self.devices.append({
                'type': 'advance_on_time',
                'user_name': 'Advance to next',
                'uuid': 'a0fac1cd-3bff-4286-80e2-20b284361ba0'
            })

        self.root = Tk()
        self.root.withdraw()
        self.device_editor_window = Toplevel(self.root)

        self.new_device_window = Tk()

        self.description_frame = Frame(self.device_editor_window, bg=bg_color)
        self.devices_listbox_frame = Frame(self.device_editor_window, bg=bg_color)
        self.bottom_buttons_frame = Frame(self.device_editor_window, bg=bg_color)

        self.devices_listbox = Listbox(self.devices_listbox_frame)

        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add ProVideoPlayer', command=self._add_pvp).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Ross Carbonite', command=self._add_ross_carbonite).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Ross NK Router', command=self._add_scpa_via_ip2sl).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add AJA KiPro', command=self._add_kipro).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Resi Decoder', command=self._add_resi).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add EZ Outlet 2', command=self._add_ez_outlet_2).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add BEM104 Relay', command=self._add_bem104).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Wave Controlflex', command=self._add_controlflex).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add AJA Kumo Router', command=self._add_aja_kumo).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Shure QLXD reciver', command=self._add_shure_qlxd).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Allen & Heath DLive Mixrack', command=self._add_ah_dlive).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add MIDI Device', command=self._add_midi).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Propresenter Device', command=self._add_propresenter).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add OBS Device', command=self._add_obs).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add WebOS TV Device', command=self._add_webos_tv).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Wake On Lan Device', command=self._add_wakeonlan).pack()

        self.new_device_window.withdraw()

    def build_ui(self):
        self.device_editor_window.configure(bg=bg_color)
        self._update_existing_devices()

        Label(self.description_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2),
              text="Use this menu to add or remove physical devices. Removing/re-adding an existing will device break it in any existing shows that you have saved!\n\n"
                   "-When finished, reload the program for your changes to take effect.\n"
                   "-You can use a devices file from a different machine or program version if you wish, just make sure it's named devices.json and in the same directory.\n", justify=LEFT).pack()

        self.devices_listbox.configure(bg=bg_color, fg=text_color, font=(font, current_cues_text_size), width=50, height=40)
        self.devices_listbox.grid(row=0, column=1)

        move_up_down_frame = Frame(self.devices_listbox_frame, bg=bg_color)
        move_up_down_frame.grid(row=0, column=0, padx=20)

        Button(move_up_down_frame, text='Move selected device up', bg=bg_color, fg=text_color, font=(font, other_text_size-2), command=self._move_selected_device_up).pack()
        Button(move_up_down_frame, text='Move selected device down', bg=bg_color, fg=text_color, font=(font, other_text_size-2), command=self._move_selected_device_down).pack()

        Button(self.bottom_buttons_frame, text='Add New Device', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self._add_new_device_window).pack(side=LEFT, padx=10)
        Button(self.bottom_buttons_frame, text='Remove Device', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self._remove_device).pack(side=LEFT, padx=10)
        Button(self.bottom_buttons_frame, text='Show details', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self._show_details).pack(side=LEFT, padx=10)
        Button(self.bottom_buttons_frame, text='Edit Device', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self._edit_device).pack(side=LEFT, padx=10)
        Button(self.bottom_buttons_frame, text='Save', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self._update_devices_file).pack(side=RIGHT, padx=10)

        self.description_frame.grid(row=0, column=0)
        self.devices_listbox_frame.grid(row=1, column=0)
        self.bottom_buttons_frame.grid(row=2, column=0)

        self.new_device_window.configure(bg=bg_color)
        self.new_device_window.title('Select a device type to add')

        self.root.mainloop()

    def build_default_file(self):
        self._update_devices_file()

    def _update_devices_file(self):
        if not os.path.exists(os.path.join('configs', 'devices_backup')):
            logger.info('devices_backup directory does not exist. Creating...')
            os.mkdir(os.path.join('configs', 'devices_backup'))

        if os.path.exists(os.path.join('configs', 'devices.json')):
            logger.info('Devices file exists, backing it up to /devices_backup')
            source_file = os.path.join('configs', 'devices.json')
            destination_file = os.path.join('configs', 'devices_backup', 'devices_BACKUP_'+ datetime.now().strftime("%Y_%m_%d-%H_%M") + '.json')

            copyfile(source_file, destination_file)
        else:
            logger.info('Devices file does not exist, nothing to back up')

        logger.info('Updating devices.json file. Contents: %s', self.devices)
        with open(os.path.join('configs', 'devices.json'), 'w') as f:
            f.writelines(json.dumps(self.devices))

        self.device_editor_window.destroy()

        tkinter.messagebox.showinfo('Saved',
                                     message=f'Changes Saved. You muse restart the main application for changes to take effect.')

        exit()

    def _add_device(self, device): # Adds date added and UUID to device info, adds to main devices dict, updates listbox
        logger.info('__add_device: received new device to add: %s', device)

        device.update({
            'uuid': str(uuid.uuid4()),
            'date_added': datetime.now().strftime("%Y_%m_%d-%H_%M")
        })

        logger.info('Adding to devices: %s', device)

        self.devices.append(device)
        self._update_existing_devices()

    def _remove_device(self):

        self.devices.pop(self.devices_listbox.curselection()[0]+3)
        self._update_existing_devices()

    def _update_existing_devices(self):
        self.devices_listbox.delete(0, 'end')

        for index, device in enumerate(self.devices):
            if not device['uuid'] in ('f0d73b84-60b1-4c1d-a49f-f3b11ea65d3f', 'b652b57e-c426-4f83-87f3-a7c4026ec1f0', '07af78bf-9149-4a12-80fc-0fa61abc0a5c', 'a0fac1cd-3bff-4286-80e2-20b284361ba0'):
                listbox_item_name = device['user_name'] + ' (' + device['type'] + ')'
                self.devices_listbox.insert(index, listbox_item_name)

    def _show_details(self): #opens new window containing details for all fields of selected device
        details_window = Tk()
        details_window.configure(bg=bg_color)
        details_window.geometry('450x250')

        selected_device_index = self._get_selected_device_index()

        for field in self.devices[selected_device_index].keys():
            Label(details_window, bg=bg_color, fg=text_color,
                  text=f'{field} : {self.devices[selected_device_index][field]}', font=(font, other_text_size)).pack()

    def _edit_device(self):
        """
        Edit the details of an existing device
        :return: None
        """
        edit_device_window = Tk()
        edit_device_window.configure(bg=bg_color)


        selected_device_index = self.devices_listbox.curselection()[0] + 3
        selected_device = self.devices[selected_device_index]

        edit_device_window.title(f'Edit {selected_device["user_name"]}')

        # We only want the user to be able to edit these aspects of the data
        editable_characteristics = {'user_name', 'ip_address', 'port', 'username', 'password', 'rosstalk_port', 'mac_address'}

        included_characteristics: set[str] = set()

        for key in selected_device.keys():
            if key in editable_characteristics:
                included_characteristics.add(key)

        user_facing_characteristic_names = {
            'ip_address': 'IP Address',
            'user_name': 'Name',
            'port': 'Port',
            'username': 'Username',
            'password': 'Password',
            'rosstalk_port': 'Rosstalk Port',
            'mac_address': 'MAC Address'
        }

        user_entry_vars = []

        for characteristic in included_characteristics:
            Label(edit_device_window, bg=bg_color, fg=text_color, font=(font, 12), text=f'{user_facing_characteristic_names[characteristic]}:').pack(anchor='w')

            user_entry = Entry(edit_device_window, bg=bg_color, font=(font, 12), fg=text_color)
            user_entry_vars.append(user_entry)
            user_entry.insert(0, selected_device[characteristic])
            user_entry.pack(anchor='w')

        def show_error(message: str) -> None:
            tkinter.messagebox.showerror('Error', message=message)

        def okay():
            is_errored = False

            for i, characteristic in enumerate(included_characteristics):
                if characteristic == 'ip_address':
                    if not self._verify_ip(user_entry_vars[i].get()):
                        is_errored = True
                        show_error('IP address not valid')
                if characteristic == 'port':
                    if not self._verify_port(user_entry_vars[i].get()):
                        is_errored = True
                        show_error('Port not valid')
                if characteristic == 'rosstalk_port':
                    if not self._verify_port(user_entry_vars[i].get()):
                        is_errored = True
                        show_error('Rosstalk port not valid')

            # change class data using Tk Entries dynamically created before
            if not is_errored:
                for i, characteristic in enumerate(included_characteristics):
                    self.devices[selected_device_index][characteristic] = user_entry_vars[i].get()

            self._update_existing_devices()
            edit_device_window.destroy()

        Button(edit_device_window, bg=bg_color, fg=text_color, font=(font, 13), text='Okay', command=okay).pack()

    def _move_selected_device_up(self):
        """
        Move the selected device up in the devices list. Useful for rearranging existing devices & reorganizing them in a more readable way.
        :return: None
        """
        device_index = self._get_selected_device_index()

        device_1 = self.devices[device_index - 1]
        device_2 = self.devices[device_index]

        self.devices[device_index] = device_1
        self.devices[device_index - 1] = device_2

        self._update_existing_devices()
        self.devices_listbox.select_set(device_index - 4)

    def _move_selected_device_down(self):

        """
        Move the selected device down in the device list. Useful for rearranging the existing devices & reorganizing them in a more readable way.
        :return:
        """

        device_index = self._get_selected_device_index()

        device_1 = self.devices[device_index]
        device_2 = self.devices[device_index + 1]

        self.devices[device_index] = device_2
        self.devices[device_index + 1] = device_1

        self._update_existing_devices()
        self.devices_listbox.select_set(device_index - 2)


    def _get_selected_device_index(self) -> int:
        """
        Get the index of the currently selected device, without the boilerplate pause, reminder, and all kipros devices.
        Bottom line, this will return the user-visible index device that's listed in the listbox.
        :return: user-visible index device that's listed in the listbox
        """
        return self.devices_listbox.curselection()[0] + 3

    def _verify_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def _verify_port(self, port):  # checks if port is a number and is between 0 and 65535
        try:
            int(port)
        except ValueError:
            return False
        if 0 < int(port) < 65535:
            return True
        else:
            return False

    def _verify_number_of_io(self, io_number):  # verifies video router input/output entry
        try:
            int(io_number)
            return True
        except ValueError:
            return False

    def _add_new_device_window(self):
        self.new_device_window.deiconify()

    def _add_pvp(self):
        self.new_device_window.withdraw()

        add_pvp = Tk()
        add_pvp.title('Add ProVideoPlayer Device')
        add_pvp.configure(bg=bg_color)
        add_pvp.geometry('400x180')

        name_entry_frame = Frame(add_pvp)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_pvp)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target IP Address:')
        port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target Port:')

        name_label.pack()
        name_entry.pack()

        ip_label.pack(side=LEFT)
        ip_address_entry.pack(side=LEFT)
        port_entry.pack(side=RIGHT)
        port_label.pack(side=RIGHT)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self._verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'pvp',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get()
                }

                self._add_device(device=to_add)
                add_pvp.destroy()
            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())

        Button(add_pvp, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_scpa_via_ip2sl(self):
        self.new_device_window.withdraw()

        add_scp = Tk()
        add_scp.title('Add SCP/A via GlobalCache IP2SL')
        add_scp.configure(bg=bg_color)
        add_scp.geometry('700x240')

        name_entry_frame = Frame(add_scp)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_scp)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        input_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        output_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_scp, bg=bg_color, fg=text_color, font=(font, other_text_size - 2),
              text="Add Ross NK router control via the Ross SCP/A, controlled by the GlobalCache IP2SL. \n"
                   "You can also add a .lbl file created by Ross Dashboard for easy labeling in the future if you'd like.")
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='GC IP2SL Target IP Address:')
        port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target Port (default 4999):')
        inputs_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Number of inputs:')
        outputs_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Number of outputs:')

        name_label.pack()
        name_entry.pack()

        device_description.pack(side=TOP)

        ip_label.grid(row=0, column=0)
        ip_address_entry.grid(row=0, column=1)

        port_label.grid(row=0, column=2)
        port_entry.grid(row=0, column=3)


        inputs_label.grid(row=1, column=0, sticky='e')
        input_entry.grid(row=1, column=1, sticky='w')

        outputs_label.grid(row=1, column=2, sticky='e')
        output_entry.grid(row=1, column=3, sticky='w')

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        nk_labels = None

        def add_nk_labels():
            path = filedialog.askopenfilename(filetypes=[('NK labels', '.lbl')])
            logger.debug('nk labels file added: %s', path)
            file = os.path.basename(path)
            nonlocal nk_labels
            nk_labels = file

            Label(add_scp, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=f'labels file added: {file}').pack(side=LEFT)

            add_scp.lift()

        def add():
            if self._verify_ip(ip_address_entry.get()) and self._verify_port(port_entry.get()) and \
                    self._verify_number_of_io(io_number=input_entry.get() and self._verify_number_of_io(io_number=output_entry.get())):

                to_add = {
                    'type': 'nk_scpa_ip2sl',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get(),
                    'inputs': input_entry.get(),
                    'outputs': output_entry.get()
                }

                if nk_labels is not None:
                    to_add['nk_labels'] = nk_labels

                self._add_device(device=to_add)
                add_scp.destroy()

            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address, port, inputs, or outputs was entered.')
                logger.error('__add_pvp: IP address, port, inputs, or outputs not valid: %s, %s, %s, %s',
                             ip_address_entry.get(), port_entry.get(), input_entry.get(), output_entry.get())
                add_scp.lift()

        Button(add_scp, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add custom NK Labels', command=add_nk_labels).pack(side=LEFT)
        Button(add_scp, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack(side=RIGHT)

    def _add_ross_carbonite(self):
        self.new_device_window.withdraw()

        add_carbonite = Tk()
        add_carbonite.title('Add Ross Carbonite Switcher')
        add_carbonite.configure(bg=bg_color)
        add_carbonite.geometry('700x220')

        Label(add_carbonite, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add Ross Carbonite switcher.\n'
                                                                                                'You can also add custom control labels here. See readme for more.').pack()

        name_entry_frame = Frame(add_carbonite)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_carbonite)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target Rosstalk IP Address:')
        port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Rosstalk Port(default 7788):')

        cc_labels = None

        def add_cc_labels():
            path = filedialog.askopenfilename(filetypes=[('OpenDocument Spreadsheet', '.ods')])
            logger.debug('carbonite custom control labels file added: %s', path)
            file = os.path.basename(path)
            nonlocal cc_labels
            cc_labels = file

            Label(add_carbonite, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=f'labels file added: {file}').pack(side=LEFT)

            add_carbonite.lift()

        name_label.pack()
        name_entry.pack()

        ip_label.pack(side=LEFT)
        ip_address_entry.pack(side=LEFT)
        port_entry.pack(side=RIGHT)
        port_label.pack(side=RIGHT)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self._verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'ross_carbonite',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get()
                }

                if cc_labels is not None:
                    to_add['cc_labels'] = cc_labels

                self._add_device(device=to_add)
                add_carbonite.destroy()
            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())

        Button(add_carbonite, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack(side=LEFT)
        Button(add_carbonite, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Custom Control Labels', command=add_cc_labels).pack(side=LEFT)

    def _add_kipro(self):
        self.new_device_window.withdraw()

        add_kipro = Tk()
        add_kipro.title('Add AJA KiPro')
        add_kipro.configure(bg=bg_color)

        Label(add_kipro, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add an AJA KiPro').pack()

        name_entries = []
        ip_entries = []

        entry_frames = Frame(add_kipro)
        entry_frames.configure(bg=bg_color)
        entry_frames.pack()

        def add_line():
            entry_frame = Frame(entry_frames)
            entry_frame.configure(bg=bg_color)
            entry_frame.pack()

            Label(entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:').pack(side=LEFT)
            name_entry = Entry(entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
            name_entries.append(name_entry)
            name_entry.pack(side=LEFT)

            Label(entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target KiPro IP Address:').pack(side=LEFT)
            ip_address_entry = Entry(entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
            ip_entries.append(ip_address_entry)
            ip_address_entry.pack(side=LEFT)

            entry_frame.pack(pady=5)

        add_line()

        def check_and_add():
            names = []
            ips = []
            checks = []

            for name, ip in zip(name_entries, ip_entries):
                logger.debug('Attempting to add name %s, ip %s', name.get(), ip.get())
                if name.get() == '' and self._verify_ip(ip=ip.get()):
                    checks.append(False)
                    messagebox.showerror(title='Enter name', message='Please enter a name for KiPro')
                    add_kipro.lift()
                elif not name.get() == '' and not ip.get() == '':
                    logger.debug('adding name %s, ip %s', name.get(), ip.get())
                    names.append(name.get())
                    ips.append(ip.get())

            for ip in ips:
                if self._verify_ip(ip=ip):
                    checks.append(True)
                else:
                    logger.error('ip %s not valid', ip)
                    checks.append(False)
                    messagebox.showerror(title='Invalid IP address',
                                         message=f'{ip} is not a valid ip address.')
                    add_kipro.lift()

            if False not in checks:
                for name, ip in zip(names, ips):
                    logger.debug('Adding kipros: %s, %s', names, ips)
                    to_add = {
                        'type': 'kipro',
                        'user_name': name,
                        'ip_address': ip
                    }
                    self._add_device(device=to_add)

                add_kipro.destroy()

        Button(add_kipro, bg=bg_color, fg=text_color, font=(font, other_text_size), text='add new line', command=add_line).pack(side=LEFT)
        Button(add_kipro, bg=bg_color, fg=text_color, font=(font, other_text_size), text='add all', command=check_and_add).pack(side=LEFT)

    def _add_resi(self):
        self.new_device_window.withdraw()

        add_resi = Tk()
        add_resi.title('Add Resi Decoder')
        add_resi.configure(bg=bg_color)
        add_resi.geometry('700x350')

        name_entry_frame = Frame(add_resi)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_resi)
        info_entry_frame.configure(bg=bg_color)

        device_description = Label(add_resi, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add a Resi Streaming Decoder')

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')

        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target Resi IP Address:')
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Resi Rosstalk Port(default 7788):')
        port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        exos_mgmt_ip_entry_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='exos management address: ')
        exos_mgmt_ip_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        exos_mgmt_user_entry_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='exos management username: ')
        exos_mgmt_user_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        exos_mgmt_pass_entry_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='exos management password: ')
        exos_mgmt_pass_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        exos_port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='resi/switch port number: ')
        exos_port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        name_label.pack()
        name_entry.pack()

        device_description.pack(side=TOP)

        ip_label.grid(row=0, column=0, pady=5)
        ip_address_entry.grid(row=0, column=1, pady=5)

        port_label.grid(row=1, column=0, pady=5)
        port_entry.grid(row=1, column=1, pady=5)

        def show_exos():
            exos_mgmt_ip_entry_label.grid(row=4, column=0, pady=5)
            exos_mgmt_ip_entry.grid(row=4, column=1, pady=5)

            exos_mgmt_user_entry_label.grid(row=5, column=0, pady=5)
            exos_mgmt_user_entry.grid(row=5, column=1, pady=5)

            exos_mgmt_pass_entry_label.grid(row=6, column=0, pady=5)
            exos_mgmt_pass_entry.grid(row=6, column=1, pady=5)

            exos_port_label.grid(row=7, column=0, pady=5)
            exos_port_entry.grid(row=7, column=1, pady=5)

            add_resi.geometry('700x500')

        exos_description = Label(add_resi, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), justify=LEFT, wraplength=600,
                                text="Since Resi Decoders are typically required to have a DHCP acquired address rather than" \
        "a static one, Service Planner can automatically get it by reading the arp entries on the physical switch port " \
        "that it's connected to. Only confirmed working on extreme x440 series switches. A target resi IP is required " \
        "even if obtain ip automatically is checked. Make sure you have telnet enabled on your switch. \n***TEST THIS BEFORE YOU USE IT IN PRODUCTION")

        obtain_automatically_status = BooleanVar(info_entry_frame)
        obtain_ip_dynamically = Checkbutton(info_entry_frame, bg=bg_color, fg=text_color, selectcolor=bg_color, font=(font, other_text_size-3),
                                            text='Obtain Resi IP Address Automatically (recommended)', command=show_exos,
                                            variable=obtain_automatically_status)

        exos_description.pack()
        obtain_ip_dynamically.grid(row=3, column=0, padx=15)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self._verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'resi',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get(),
                    'obtain_ip_automatically': obtain_automatically_status.get()
                }

                if obtain_automatically_status.get():
                    if self._verify_ip(exos_mgmt_ip_entry.get()):
                        to_add.update({
                            'exos_mgmt_ip': exos_mgmt_ip_entry.get(),
                            'exos_mgmt_user': exos_mgmt_user_entry.get(),
                            'exos_mgmt_pass': exos_mgmt_pass_entry.get(),
                            'resi_exos_port': exos_port_entry.get()
                        })

                else:
                    messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                    logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())
                    add_resi.lift()

                self._add_device(device=to_add)
                add_resi.destroy()

            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())
                add_resi.lift()

        Button(add_resi, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_ez_outlet_2(self):
        self.new_device_window.withdraw()

        add_ez = Tk()
        add_ez.title('Add Resi Decoder')
        add_ez.configure(bg=bg_color)
        add_ez.geometry('800x300')

        name_entry_frame = Frame(add_ez)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_ez)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        username_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        password_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_ez, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add an EZ Outlet 2')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target IP Address:')
        username_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Control Username (default admin):')
        password_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Control Password (default admin):')

        device_description.pack()

        name_label.grid(row=0, column=0, padx=10, pady=10)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ip_label.grid(row=0, column=0, padx=10, pady=10)
        ip_address_entry.grid(row=0, column=1, padx=10, pady=10)

        username_label.grid(row=1, column=0, padx=10, pady=10)
        username_entry.grid(row=1, column=1, padx=10, pady=10)

        password_label.grid(row=1, column=2, padx=10, pady=10)
        password_entry.grid(row=1, column=3, padx=10, pady=10)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self._verify_ip(ip_address_entry.get()):

                to_add = {
                    'type': 'ez_outlet_2',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'username': username_entry.get(),
                    'password': password_entry.get()
                }

                self._add_device(device=to_add)
                add_ez.destroy()
            else:
                messagebox.showerror(title='Invalid IP address', message='An Invalid IP address was entered')
                logger.error('__add_pvp: IP address not valid: %s', ip_address_entry.get())
                add_ez.lift()

        Button(add_ez, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_bem104(self):
        self.new_device_window.withdraw()

        add_ez = Tk()
        add_ez.title('Add BEM104 Relay')
        add_ez.configure(bg=bg_color)
        add_ez.geometry('800x300')

        name_entry_frame = Frame(add_ez)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_ez)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color,
                           font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color,
                                 font=(font, current_cues_text_size))

        device_description = Label(add_ez, bg=bg_color, fg=text_color, font=(font, other_text_size - 2),
                                   text='Add BEM104 Relay')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2),
                         text='Target IP Address:')

        device_description.pack()

        name_label.grid(row=0, column=0, padx=10, pady=10)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ip_label.grid(row=0, column=0, padx=10, pady=10)
        ip_address_entry.grid(row=0, column=1, padx=10, pady=10)


        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self._verify_ip(ip_address_entry.get()):

                to_add = {
                    'type': 'bem104',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get()
                }

                self._add_device(device=to_add)
                add_ez.destroy()
            else:
                messagebox.showerror(title='Invalid IP address', message='An Invalid IP address was entered')
                logger.error('__add_bem104 relay: IP address not valid: %s', ip_address_entry.get())
                add_ez.lift()

        Button(add_ez, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_controlflex(self):
        self.new_device_window.withdraw()

        add_controlflex = Tk()
        add_controlflex.title('Add Wave Controlfex')
        add_controlflex.configure(bg=bg_color)

        name_entry_frame = Frame(add_controlflex)
        name_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(name_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_controlflex, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add Wave Controlflex')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Controlflex IP Address:')

        device_description.grid(row=0, column=0) # parent is main window

        name_label.grid(row=0, column=0, padx=10, pady=10)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ip_label.grid(row=1, column=0, padx=10, pady=10)
        ip_address_entry.grid(row=1, column=1, padx=10, pady=10)

        name_entry_frame.grid(row=1, column=0) # parent is main window

        info_entry_canvas = Canvas(add_controlflex, bg=bg_color, width=900, height=800, highlightthickness=0)
        info_entry_canvas.grid(row=2, column=0) # parent is main window

        info_entry_frame = Frame(info_entry_canvas, width=500, height=10000, bg=bg_color)  # frame to hold all controlflex zones

        canvas_scroll = Scrollbar(add_controlflex, command=info_entry_canvas.yview)
        canvas_scroll.grid(row=2, column=2, sticky='nsew')  # parent is main window

        info_entry_canvas.create_window(0, 0, anchor='nw', window=info_entry_frame) #Create window in canvas to hold info entry frame

        info_entry_canvas.configure(scrollregion=info_entry_canvas.bbox('all'), yscrollcommand=canvas_scroll.set) # set scroll of canvas

        zone_frames = []

        zone_data = []  # All zone data is added here. Each zone is a dict

        zones = 0
        def add_zone(): #add a new controlflex zone
            nonlocal zones
            zones += 1

            zone_frame = Frame(info_entry_frame, bg=bg_color)
            zone_frames.append(zone_frame)
            zone_frame.grid(row=zones+1, column=1, pady=10)

            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-2), text='Controlflex zone type:').grid(row=0, column=0)

            zone_type_options = ['Sony Pro Bravia', 'QSys Zone']
            zone_type = StringVar(zone_frame)
            zone_type.set(zone_type_options[0])

            zone_type_dropdown = OptionMenu(zone_frame, zone_type, *zone_type_options)
            zone_type_dropdown.grid(row=0, column=1)

            def update_zone(): # controlflex zone has been selected
                zone_type_set = zone_type.get()

                zone_type_dropdown.destroy()
                Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2),text=zone_type_set).grid(row=0, column=1) # When a controlflex zone is selected, the dropdown menu is destroyed to prevent user from changing it

                if zone_type_set == 'Sony Pro Bravia':
                    sony_label = Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-2), text='Sony Pro Bravia Name in controlflex config:')
                    sony_pro_bravia_name = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                    sony_label.grid(row=1, column=0, padx=10)
                    sony_pro_bravia_name.grid(row=1, column=1, padx=10)

                    friendly_sony_label = Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size-2), text='Friendly TV name:')
                    friendly_sony_name = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                    friendly_sony_label.grid(row=2, column=0, padx=10)
                    friendly_sony_name.grid(row=2, column=1, padx=10)

                    def ok():
                        sony_pro_bravia_name_entry = sony_pro_bravia_name.get()
                        sony_pro_bravia_name.destroy()
                        Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=sony_pro_bravia_name_entry).grid(row=1, column=1)

                        sony_pro_bravia_friendly_name_entry = friendly_sony_name.get()
                        friendly_sony_name.destroy()
                        Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=sony_pro_bravia_friendly_name_entry).grid(row=2, column=1)

                        zone_data.append({
                            'zone_type': 'sony_pro_bravia',
                            'flex_name': sony_pro_bravia_name_entry,
                            'friendly_name': sony_pro_bravia_friendly_name_entry
                        })

                    sony_pro_bravia_okay = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=lambda: (ok(), sony_pro_bravia_okay.destroy()))
                    sony_pro_bravia_okay.grid(row=1, column=2, padx=5)

                if zone_type_set == 'QSys Zone':
                    Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='QSys Zone Type: ').grid(row=1, column=0)

                    qsys_device_name_label = Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Qsys device name in ControlFlex: ')
                    qsys_device_name_label.grid(row=1, column=2)
                    controlflex_qsys_name_entry = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                    controlflex_qsys_name_entry.grid(row=1, column=3)

                    qsys_zone_types = ['Gain', 'Mute', 'Source']
                    qsys_zone_type = StringVar(zone_frame)
                    qsys_zone_type.set(qsys_zone_types[0])
                    qsys_zone_type_dropdown = OptionMenu(zone_frame, qsys_zone_type, *qsys_zone_types)
                    qsys_zone_type_dropdown.grid(row=1, column=1, padx=10)

                    def update_qsys_zone(): # qsys zone type selected
                        qsys_zone = qsys_zone_type.get()
                        controlflex_qsys_name = controlflex_qsys_name_entry.get()
                        qsys_ui_name = f'{controlflex_qsys_name} ({qsys_zone})'

                        qsys_zone_type_dropdown.destroy()
                        qsys_device_name_label.destroy()
                        controlflex_qsys_name_entry.destroy()

                        Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=qsys_ui_name).grid(row=1, column=1)

                        if qsys_zone == 'Gain':
                            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='QSys Control ID listed in Controlflex UI: ').grid(row=2, column=0)
                            qsys_control_id = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                            qsys_control_id.grid(row=2, column=1)

                            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Friendly Zone Name: ').grid(row=3, column=0)
                            friendly_zone_name = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                            friendly_zone_name.grid(row=3, column=1)

                            def ok():  # okay clicked on gain qsys control id
                                qsys_control_id_entry = qsys_control_id.get()
                                friendly_zone_name_entry = friendly_zone_name.get()

                                qsys_control_id.destroy()
                                friendly_zone_name.destroy()

                                Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=qsys_control_id_entry).grid(row=2, column=1)
                                Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=friendly_zone_name_entry).grid(row=3, column=1)

                                zone_data.append({
                                    'zone_type': 'qsys',
                                    'qsys_name': controlflex_qsys_name,
                                    'qsys_zone_type': 'qsys_gain',
                                    'control_id': qsys_control_id_entry,
                                    'friendly_name': friendly_zone_name_entry
                                })

                            qsys_zone_okay = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=lambda: (ok(), qsys_zone_okay.destroy()))
                            qsys_zone_okay.grid(row=3, column=3, padx=5)

                        if qsys_zone == 'Mute':
                            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='QSys Control ID listed in Controlflex UI: ').grid(row=2, column=0)
                            qsys_control_id = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                            qsys_control_id.grid(row=2, column=1)

                            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Friendly Zone Name: ').grid(row=3, column=0)
                            friendly_zone_name = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                            friendly_zone_name.grid(row=3, column=1)

                            def ok():  # okay clicked on mute qsys control id
                                qsys_control_id_entry = qsys_control_id.get()
                                friendly_zone_name_entry = friendly_zone_name.get()

                                qsys_control_id.destroy()
                                friendly_zone_name.destroy()

                                Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=qsys_control_id_entry).grid(row=2, column=1)
                                Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=friendly_zone_name_entry).grid(row=3, column=1)

                                zone_data.append({
                                    'zone_type': 'qsys',
                                    'qsys_name': controlflex_qsys_name,
                                    'qsys_zone_type': 'qsys_mute',
                                    'control_id': qsys_control_id_entry,
                                    'friendly_name': friendly_zone_name_entry
                                })

                            qsys_zone_okay = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=lambda: (ok(), qsys_zone_okay.destroy()))
                            qsys_zone_okay.grid(row=3, column=3, padx=5)

                        if qsys_zone == 'Source':
                            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='QSys Control ID listed in Controlflex UI: ').grid(row=2, column=0)
                            qsys_control_id = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                            qsys_control_id.grid(row=2, column=1)

                            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Friendly Zone Name: ').grid(row=3, column=0)
                            friendly_zone_name = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                            friendly_zone_name.grid(row=3, column=1)

                            def ok():  # okay clicked on source qsys control id
                                qsys_control_id_entry = qsys_control_id.get()
                                friendly_zone_name_entry = friendly_zone_name.get()

                                qsys_control_id.destroy()
                                friendly_zone_name.destroy()

                                Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=qsys_control_id_entry).grid(row=2, column=1)
                                Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=friendly_zone_name_entry).grid(row=3, column=1)

                                source_name_entries = []  # add source name entries to this list so they can be destroyed later and replaced with a label when ok is pressed
                                source_names = [] # friendly input name of each source. postion 0 in list is input 1 in controlflex

                                inputs = 0
                                def add_input():
                                    nonlocal inputs
                                    inputs += 1

                                    Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=f'Input #{inputs} in ControlFlex. Friendly Input Name:  ').grid(row=3+inputs, column=0)

                                    input_name_entry = Entry(zone_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
                                    input_name_entry.grid(row=3+inputs, column=1)
                                    source_name_entries.append(input_name_entry)

                                    def input_added(): # destroys buttons for current source
                                        input_okay.destroy()
                                        add_input_button.destroy()

                                    def finished_with_source_inputs(): # destroys all source entry boxes and replaces them with what was entered. Destroys okay/add buttons. Adds entered qsys sources to zone_data list
                                        for input_entry in source_name_entries:
                                            grid_info = input_entry.grid_info()
                                            Label(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text=input_entry.get()).grid(row=grid_info['row'], column=grid_info['column'])
                                            source_names.append(input_entry.get())
                                            input_entry.destroy()
                                        input_added()

                                        zone_data.append({
                                            'zone_type': 'qsys',
                                            'qsys_name': controlflex_qsys_name,
                                            'qsys_zone_type': 'qsys_source',
                                            'control_id': qsys_control_id_entry,
                                            'friendly_name': friendly_zone_name_entry,
                                            'friendly_input_names': source_names
                                        })

                                    add_input_button = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Another Input', command=lambda: (add_input(), input_added()))
                                    add_input_button.grid(row=3 + inputs, column=2)

                                    input_okay = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Finished with inputs', command=finished_with_source_inputs)
                                    input_okay.grid(row=3+inputs, column=3)

                                add_input()

                            qsys_zone_okay = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=lambda: (ok(), qsys_zone_okay.destroy()))
                            qsys_zone_okay.grid(row=3, column=3, padx=5)

                    qsys_okay = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=lambda: (update_qsys_zone(), qsys_okay.destroy()))
                    qsys_okay.grid(row=1, column=4, padx=10)

            zone_okay = Button(zone_frame, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Okay', command=lambda: (update_zone(), zone_okay.destroy()))
            zone_okay.grid(row=0, column=2, padx=10)

        def finished():
            self._add_device(device={
                'type': 'controlflex',
                'user_name': name_entry.get(),
                'ip_address': ip_address_entry.get(),
                'zones': zone_data
            })
            add_controlflex.destroy()

        Button(add_controlflex, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add new Zone', command=add_zone).grid()  # add new controlflex zone, parent is main window
        Button(add_controlflex, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Finished: add controlflex device and all zones', command=finished).grid()  # Add controlflex device. Pressed when finished, parent is main window

    def _add_aja_kumo(self):
        self.new_device_window.withdraw()

        add_kumo = Tk()
        add_kumo.title('Add AJA Kumo Router')
        add_kumo.configure(bg=bg_color)
        add_kumo.geometry('500x200')

        name_entry_frame = Frame(add_kumo)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_kumo)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_kumo, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add AJA Kumo Video Router')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target IP Address:')

        device_description.pack()

        name_label.grid(row=0, column=0, padx=10, pady=10)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ip_label.grid(row=0, column=0, padx=10, pady=10)
        ip_address_entry.grid(row=0, column=1, padx=10, pady=10)

        name_entry_frame.pack(pady=10)
        info_entry_frame.pack(pady=10)

        def add():
            if self._verify_ip(ip_address_entry.get()):

                to_add = {
                    'type': 'aja_kumo',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get()
                }

                self._add_device(device=to_add)
                add_kumo.destroy()
            else:
                messagebox.showerror(title='Invalid IP address', message='An Invalid IP address was entered')
                logger.error('__add_aja_kumo: IP address not valid: %s', ip_address_entry.get())
                add_kumo.lift()

        Button(add_kumo, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_shure_qlxd(self):
        self.new_device_window.withdraw()

        add_qlxd = Tk()
        add_qlxd.title('Add a Shure QLXD receiver')
        add_qlxd.configure(bg=bg_color)
        add_qlxd.geometry('500x600')

        name_entry_frame = Frame(add_qlxd)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_qlxd)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_qlxd, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add Shure QLXD Wireless Microphone Receiver')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target IP Address:')

        channel_description_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Channel Names (leave empty for none)')
        channel_description_label.grid(row=1, column=0)


        device_description.pack()

        name_label.grid(row=0, column=0, padx=10, pady=10)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ip_label.grid(row=0, column=0, padx=10, pady=15)
        ip_address_entry.grid(row=0, column=1, padx=10, pady=15)

        name_entry_frame.pack(pady=5)
        info_entry_frame.pack(pady=5)

        def add():
            if self._verify_ip(ip_address_entry.get()):
                to_add = {
                    'type': 'shure_qlxd',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                }

                self._add_device(device=to_add)
                add_qlxd.destroy()
            else:
                messagebox.showerror(title='Invalid IP address', message='An Invalid IP address was entered')
                logger.error('__add_shure_qlxd: IP address not valid: %s', ip_address_entry.get())
                add_qlxd.lift()

        Button(add_qlxd, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_ah_dlive(self):
        self.new_device_window.withdraw()

        add_ah_dlive = Tk()
        add_ah_dlive.title('Add Allen Heath DLive MixRack')
        add_ah_dlive.configure(bg=bg_color)
        add_ah_dlive.geometry('550x200')

        name_entry_frame = Frame(add_ah_dlive)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_ah_dlive)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_ah_dlive, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add a Allen & Heath DLive MixRack')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target IP Address:')

        def add():
            if self._verify_ip(ip_address_entry.get()):

                to_add = {
                    'type': 'ah_dlive',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get()
                }

                self._add_device(device=to_add)
                add_ah_dlive.destroy()
            else:
                messagebox.showerror(title='Invalid IP address', message='An Invalid IP address was entered')
                logger.error('__add_shure_qlxd: IP address not valid: %s', ip_address_entry.get())
                add_ah_dlive.lift()

        device_description.pack()

        name_label.grid(row=0, column=0, padx=10, pady=10)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ip_label.grid(row=0, column=0, padx=10, pady=15)
        ip_address_entry.grid(row=0, column=1, padx=10, pady=15)

        name_entry_frame.pack(pady=5)
        info_entry_frame.pack(pady=5)

        Button(add_ah_dlive, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_midi(self):
        self.new_device_window.withdraw()

        add_midi = Tk()
        add_midi.title('Add Midi Device')
        add_midi.configure(bg=bg_color)
        add_midi.geometry('550x200')

        name_entry_frame = Frame(add_midi)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_midi)
        info_entry_frame.configure(bg=bg_color)

        device_description = Label(add_midi, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add a MIDI device')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        midi_types = [
            'ProPresenter',
            'Other/Custom'
        ]

        midi_type_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Type of MIDI device:')
        midi_type_label.grid(row=0, column=0)

        midi_type_selected = StringVar(info_entry_frame)
        midi_type_selected.set(midi_types[0])

        midi_types_dropdown = OptionMenu(info_entry_frame, midi_type_selected, *midi_types)
        midi_types_dropdown.grid(row=0, column=1)

        midi_interface = Midi()
        midi_interfaces = midi_interface.get_midi_out()

        midi_interface_selected = StringVar(info_entry_frame)
        midi_interface_selected.set(midi_interfaces[0])

        midi_interface_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='MIDI Interface:')
        midi_interface_label.grid(row=1, column=0)

        midi_interfaces_dropdown = OptionMenu(info_entry_frame, midi_interface_selected, *midi_interfaces)
        midi_interfaces_dropdown.grid(row=1, column=1)

        def add():
            to_add = {
                'type': 'midi',
                'midi_type': midi_type_selected.get(),
                'user_name': name_entry.get(),
                'midi_device': midi_interface_selected.get()
            }

            self._add_device(device=to_add)
            add_midi.destroy()

        device_description.pack()

        name_label.grid(row=0, column=0, padx=10, pady=10)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        name_entry_frame.pack(pady=5)
        info_entry_frame.pack(pady=5)

        Button(add_midi, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_propresenter(self):
        self.new_device_window.withdraw()

        add_propresenter = Tk()
        add_propresenter.title('Add ProVideoPlayer Device')
        add_propresenter.configure(bg=bg_color)
        add_propresenter.geometry('400x180')

        name_entry_frame = Frame(add_propresenter)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_propresenter)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target IP Address:')
        port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target Port:')

        name_label.pack()
        name_entry.pack()

        ip_label.pack(side=LEFT)
        ip_address_entry.pack(side=LEFT)
        port_entry.pack(side=RIGHT)
        port_label.pack(side=RIGHT)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self._verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'propresenter',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get()
                }

                self._add_device(device=to_add)
                add_propresenter.destroy()
            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())

        Button(add_propresenter, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_obs(self):
        self.new_device_window.withdraw()

        add_obs = Tk()
        add_obs.title('Add OBS device')
        add_obs.configure(bg=bg_color)
        add_obs.geometry('400x180')

        name_frame = Frame(add_obs, bg=bg_color)
        ip_address_frame = Frame(add_obs, bg=bg_color)

        name_entry = Entry(name_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(ip_address_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        name_label = Label(name_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(ip_address_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='IP Address:')

        name_label.pack(side=LEFT)
        name_entry.pack(side=RIGHT)

        ip_label.pack(side=LEFT)
        ip_address_entry.pack(side=RIGHT)

        name_frame.pack(pady=20)
        ip_address_frame.pack(pady=20)

        def okay():
            if self._verify_ip(ip=ip_address_entry.get()):
                to_add = {
                    'type': 'obs',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get()
                }
                self._add_device(device=to_add)
                add_obs.destroy()
            else:
                messagebox.showerror(title='Invalid IP address', message='An Invalid IP address was entered')

        Button(add_obs, text='Okay', bg=bg_color, fg=text_color, font=(font, current_cues_text_size), command=okay).pack()


    def _add_webos_tv(self):
        self.new_device_window.withdraw()

        add_webos_tv = Tk()
        add_webos_tv.title = ('Add LG Smart TV')
        add_webos_tv.configure(bg=bg_color)
        add_webos_tv.geometry('400x180')

        name_entry_frame = Frame(add_webos_tv)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_webos_tv)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='IP Address:')

        name_label.pack()
        name_entry.pack()

        ip_label.pack(side=LEFT)
        ip_address_entry.pack(side=LEFT)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self._verify_ip(ip_address_entry.get()):
                to_add = {
                    'type': 'webostv',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get()
                }

                self._add_device(device=to_add)
                add_webos_tv.destroy()
            else:
                messagebox.showerror(title='Invalid IP address', message='An invalid IP Address was entered')

        Button(add_webos_tv, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def _add_wakeonlan(self):

        self.new_device_window.withdraw()

        add_wakeonlan = Tk()
        add_wakeonlan.title = ('Add Wake On Lan')
        add_wakeonlan.configure(bg=bg_color)
        add_wakeonlan.geometry('500x200')

        name_entry_frame = Frame(add_wakeonlan)
        name_entry_frame.configure(bg=bg_color)

        info_frame = Frame(add_wakeonlan)
        info_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_wakeonlan)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        mac_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        mac_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='MAC Address of target:')


        Label(info_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='The destination device must be in the same broadcast domain.\nCrossing a routed network will generally not work.').pack()

        name_label.pack()
        name_entry.pack()

        mac_label.pack(side=LEFT)
        mac_address_entry.pack(side=LEFT)

        name_entry_frame.pack(pady=10)
        info_frame.pack()
        info_entry_frame.pack(pady=10)

        def add():
            if is_mac_address_valid(mac_address_entry.get()):
                to_add = {
                    'type': 'wakeonlan',
                    'user_name': name_entry.get(),
                    'mac_address': mac_address_entry.get()
                }

                self._add_device(device=to_add)
                add_wakeonlan.destroy()
            else:
                messagebox.showerror(title='Invalid MAC address', message='An invalid MAC Address was entered')

        Button(add_wakeonlan, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()


if __name__ == '__main__':
    device_editor = DeviceEditor()
    device_editor.build_ui()