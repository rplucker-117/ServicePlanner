import os
import json
from logzero import logger
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from settings import *
import uuid
import socket
from datetime import datetime
from shutil import copyfile

class DeviceEditor:
    def __init__(self):
        if os.path.exists('devices.json'):
            logger.debug('DeviceEditor.__init__: devices.json exists. Reading...')
            with open('devices.json', 'r') as f:
                self.devices = json.loads(f.read())
            logger.debug('DeviceEditor.__init__: devices.json contents: %s', self.devices)
        else:
            logger.info('DeviceEditor.__init__: devices.json does not exist. Setting to empty list.')
            self.devices = []

        self.device_editor_window = Tk()
        self.devices_listbox = Listbox(self.device_editor_window)

        self.new_device_window = Tk()
        self.new_device_window.configure(bg=bg_color)

        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add ProVideoPlayer', command=self.__add_pvp).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Ross Carbonite', command=self.__add_ross_carbonite).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Ross NK Router', command=self.__add_scpa_via_ip2sl).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add AJA KiPro', command=self.__add_kipro).pack()
        Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Resi Decoder', command=self.__add_resi).pack()
        # Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add AJA IPT').pack()
        # Button(self.new_device_window, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add AJA IPR').pack()

        self.new_device_window.withdraw()

    def build_ui(self):
        self.device_editor_window.configure(bg=bg_color)
        self.__update_existing_devices()

        Label(self.device_editor_window, bg=bg_color, fg=text_color, font=(font, other_text_size - 2),
              text="Use this menu to add or remove physical devices. Removing/re-adding an existing will device break it in any existing shows that you have saved!\n\n"
                   "-It's recommended that you make a backup of your devices.json file. One will be made for you in devices_backup/ upon save.\n"
                   "-When finished, reload the program for your changes to take effect.\n"
                   "-You can use a devices file from a different machine or program version if you wish, just make sure it's named devices.json and in the same directory.\n", justify=LEFT).pack()

        self.devices_listbox.configure(bg=bg_color, fg=text_color, font=(font, current_cues_text_size), width=50)
        self.devices_listbox.pack(pady=20)

        Button(self.device_editor_window, text='Add New Device', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self.__add_new_device_window).pack(side=LEFT, padx=10)
        Button(self.device_editor_window, text='Remove Device', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self.__remove_device).pack(side=LEFT, padx=10)
        Button(self.device_editor_window, text='Write changes to disk', bg=bg_color, fg=text_color, font=(font, other_text_size), padx=5, command=self.__update_devices_file).pack(side=RIGHT, padx=10)

        self.device_editor_window.mainloop()

    def __update_devices_file(self):
        if not os.path.exists('devices_backup/'):
            logger.info('devices_backup directory does not exist. Creating...')
            os.mkdir('devices_backup/')

        if os.path.exists('devices.json'):
            logger.info('Devices file exists, backing it up to /devices_backup')
            copyfile('devices.json', 'devices_backup/devices_BACKUP_' + datetime.now().strftime("%Y_%m_%d-%H_%M") + '.json')
        else:
            logger.info('Devices file does not exist, nothing to back up')

        logger.info('Updating devices.json file. Contents: %s', self.devices)
        with open ('devices.json', 'w') as f:
            f.writelines(json.dumps(self.devices))

    def __add_device(self, device):
        # Adds date added and UUID to device info, adds to main devices dict, updates listbox
        logger.info('__add_device: received new device to add: %s', device)

        device.update({
            'uuid': str(uuid.uuid4()),
            'date_added': datetime.now().strftime("%Y_%m_%d-%H_%M")
        })

        logger.info('Adding to devices: %s', device)

        self.devices.append(device)
        self.__update_existing_devices()

    def __remove_device(self):
        self.devices.pop(self.devices_listbox.curselection()[0])
        self.__update_existing_devices()

    def __update_existing_devices(self):
        self.devices_listbox.delete(0, 'end')

        for index, device in enumerate(self.devices):
            listbox_item_name = device['user_name'] + ' (' + device['type'] + ')'
            self.devices_listbox.insert(index, listbox_item_name)

    def __verify_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def __add_new_device_window(self):
        self.new_device_window.deiconify()

    def __add_pvp(self):
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
            if self.__verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'pvp',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get()
                }

                self.__add_device(device=to_add)
                add_pvp.destroy()
            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())

        Button(add_pvp, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def __add_scpa_via_ip2sl(self):
        self.new_device_window.withdraw()

        add_scp = Tk()
        add_scp.title('Add SCP/A via GlobalCache IP2SL')
        add_scp.configure(bg=bg_color)
        add_scp.geometry('700x200')

        name_entry_frame = Frame(add_scp)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_scp)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_scp, bg=bg_color, fg=text_color, font=(font, other_text_size - 2),
              text='Add Ross NK router control via the Ross SCP/A, controlled by the GlobalCache IP2SL. See readme for more info')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='GC IP2SL Target IP Address:')
        port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target Port (default 4999):')

        name_label.pack()
        name_entry.pack()

        device_description.pack(side=TOP)
        ip_label.pack(side=LEFT)
        ip_address_entry.pack(side=LEFT)
        port_entry.pack(side=RIGHT)
        port_label.pack(side=RIGHT)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self.__verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'nk_scpa_ip2sl',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get()
                }

                self.__add_device(device=to_add)
                add_scp.destroy()
            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())
                add_scp.lift()

        Button(add_scp, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

    def __add_ross_carbonite(self):
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
            if self.__verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'ross_carbonite',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get()
                }

                self.__add_device(device=to_add)
                add_carbonite.destroy()
            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())

        Button(add_carbonite, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack(side=LEFT)
        Button(add_carbonite, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add Custom Control Labels', command=add_cc_labels).pack(side=LEFT)

    def __add_kipro(self):
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
                if name.get() == '' and self.__verify_ip(ip=ip.get()):
                    checks.append(False)
                    messagebox.showerror(title='Enter name', message='Please enter a name for KiPro')
                    add_kipro.lift()
                elif not name.get() == '' and not ip.get() == '':
                    logger.debug('adding name %s, ip %s', name.get(), ip.get())
                    names.append(name.get())
                    ips.append(ip.get())

            for ip in ips:
                if self.__verify_ip(ip=ip):
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
                    self.__add_device(device=to_add)

                add_kipro.destroy()

        Button(add_kipro, bg=bg_color, fg=text_color, font=(font, other_text_size), text='add new line', command=add_line).pack(side=LEFT)
        Button(add_kipro, bg=bg_color, fg=text_color, font=(font, other_text_size), text='add all', command=check_and_add).pack(side=LEFT)

    def __add_resi(self):
        self.new_device_window.withdraw()

        add_resi = Tk()
        add_resi.title('Add Resi Decoder')
        add_resi.configure(bg=bg_color)
        add_resi.geometry('700x200')

        name_entry_frame = Frame(add_resi)
        name_entry_frame.configure(bg=bg_color)

        info_entry_frame = Frame(add_resi)
        info_entry_frame.configure(bg=bg_color)

        name_entry = Entry(name_entry_frame, width=30, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        ip_address_entry = Entry(info_entry_frame, width=16, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))
        port_entry = Entry(info_entry_frame, width=5, bg=text_entry_box_bg_color, fg=text_color, font=(font, current_cues_text_size))

        device_description = Label(add_resi, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Add a Resi Streaming Decoder')
        name_label = Label(name_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Name:')
        ip_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Target Resi IP Address:')
        port_label = Label(info_entry_frame, bg=bg_color, fg=text_color, font=(font, other_text_size - 2), text='Resi Rosstalk Port(default 7788):')

        name_label.pack()
        name_entry.pack()

        device_description.pack(side=TOP)
        ip_label.pack(side=LEFT)
        ip_address_entry.pack(side=LEFT)
        port_entry.pack(side=RIGHT)
        port_label.pack(side=RIGHT)

        name_entry_frame.pack(pady=20)
        info_entry_frame.pack(pady=20)

        def add():
            if self.__verify_ip(ip_address_entry.get()) and port_entry.get() != '':

                to_add = {
                    'type': 'resi',
                    'user_name': name_entry.get(),
                    'ip_address': ip_address_entry.get(),
                    'port': port_entry.get()
                }

                self.__add_device(device=to_add)
                add_resi.destroy()
            else:
                messagebox.showerror(title='Invalid IP address or Port', message='An Invalid IP address or port was entered')
                logger.error('__add_pvp: IP address or port not valid: %s, %s', ip_address_entry.get(), port_entry.get())
                add_resi.lift()

        Button(add_resi, bg=bg_color, fg=text_color, font=(font, other_text_size), text='Add', command=add).pack()

if __name__ == '__main__':
    device_editor = DeviceEditor()
    device_editor.build_ui()