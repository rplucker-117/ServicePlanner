import urllib.request
import urllib.parse
from configs.settings import *
import json
import time
import requests
from logzero import logger
from datetime import datetime
# import demjson3 as demjson
import os
from tkinter import filedialog
import wget
from device_editor import DeviceEditor


class KiPro:
    def __init__(self):
        pass

    def set_clip_name(self, ip, name):
        logger.debug('Setting kipro clip name. ip: %s, name: %s', ip, name)
        payload = f'paramName=eParamID_CustomClipName&newValue={name}'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def set_rec_play_mode(self, ip):
        logger.debug('Setting kipro %s to rec/play mode', ip)
        payload = 'paramName=eParamID_MediaState&newValue=0'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def set_data_lan_mode(self, ip):
        logger.debug('Setting kipro %s to rec/play mode', ip)
        payload = 'paramName=eParamID_MediaState&newValue=1'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def format_current_slot(self, ip):
        logger.debug('Formatting current slot for kipro %s', ip)
        payload = 'paramName=eParamID_FormatMedia&newValue=1'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def transport_record(self, ip):
        logger.debug('Setting transport record on kipro %s', ip)
        payload= 'paramName=eParamID_TransportCommand&newValue=3'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def transport_stop(self, ip):
        self.set_rec_play_mode(ip=ip)
        logger.debug('Setting transport stop on kipro %s', ip)
        payload= 'paramName=eParamID_TransportCommand&newValue=4'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    # Returns 1 if idle, 2 if recording, 17 if error in record, 18 if unable to communicate
    def get_status(self, ip):
        # logger.debug('Getting status of kipro %s', ip)
        try:
            r = json.loads(requests.get(f'http://{ip}/config?action=get&paramid=eParamID_TransportState', timeout=kipro_timeout_threshold).text)
            # logger.debug('Status of kipro %s is %s', ip, r['value'])
            return r['value']
        except requests.exceptions.RequestException as e:
            # logger.error('Error with kipro %s. \n %s', ip, e)
            return '18'

    def get_remaining_storage(self, ip):
        # logger.debug('Getting remaining storage for kipro %s', ip)
        try:
            r = json.loads(requests.get(f'http://{ip}/config?action=get&paramid=eParamID_CurrentMediaAvailable', timeout=kipro_timeout_threshold).text)
            # logger.debug('Remaining storage on kipro %s is %s percent.', ip, r['value'])
            return r['value']
        except requests.exceptions.RequestException as e:
            return 0

    def start_absolute(self, ip, name, include_date=True):
        if include_date is True:
            now = datetime.now().strftime("_%Y_%m_%d-%H_%M")
            name = f'{name}{now}'
        self.set_clip_name(ip=ip, name=name)
        self.set_rec_play_mode(ip=ip)
        self.transport_record(ip=ip)

    def toggle_start_stop(self, ip, name, include_date=True, delay=.3):
        status = self.get_status(ip=ip)
        if status == '1':
            self.start_absolute(ip=ip, name=name, include_date=include_date)
        if status == '2':
            self.transport_stop(ip=ip)
        time.sleep(delay)

    def download_clips(self):
        kipros = []

        devices = DeviceEditor().devices
        for device in devices:
            if device['type'] == 'kipro' and not device['user_name'] == 'All Kipros':
                kipros.append(device)

        files = []

        for kipro in kipros:
            self.set_data_lan_mode(ip=kipro['ip_address'])
            r = requests.get(f"http://{kipro['ip_address']}/clips")

            returned_data = r.text[:-2]

            #returned_data looks like """[
                # { clipname: "REC1_2024_05_26-09_56_1.mov", timestamp: "05/26/24 08:38:47", fourcc: "apcs", width: "1920", height: "1080", framecount: "150568", framerate: "29.97", interlace: "1" }
                # , { clipname: "REC1_2024_05_26-11_26_1.mov", timestamp: "05/26/24 10:10:36", fourcc: "apcs", width: "1920", height: "1080", framecount: "153863", framerate: "29.97", interlace: "1" }
                # ]"""

            for old_word, new_word in zip(
                    ('clipname', 'timestamp', 'fourcc', 'width', 'height', 'framecount', 'framerate', 'interlace'),
                    (r'"clipname"', '"timestamp"', '"fourcc"', '"width"', '"height"', '"framecount"', '"framerate"', '"interlace"')):
                returned_data = returned_data.replace(old_word, new_word)

            clips = json.loads(returned_data)

            files.append({
                'clips': clips,
                'ip': kipro['ip_address']
            })

        os.chdir(filedialog.askdirectory())

        for recorder in files:
            for clip in recorder['clips']:
                url = f"http://{recorder['ip']}/media/{clip['clipname']}"
                logger.info('Downloading clip %s from %s', clip['clipname'], url)
                wget.download(url, clip['clipname'])
        logger.info('\nAll downloads complete')


if __name__ == '__main__':
    kipro = KiPro()
    kipro.download_clips()