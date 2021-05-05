import urllib.request
import urllib.parse
from settings import *
import json
import time
import requests
from logzero import logger
from datetime import datetime
import demjson
import os
from tkinter import filedialog
from tkinter import *
import wget
import pprint
import threading


# logger.basicConfig(level=log_level)

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
        logger.debug('Setting transport stop on kipro %s', ip)
        payload= 'paramName=eParamID_TransportCommand&newValue=4'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    # Returns 1 if idle, 2 if recording, 17 if error in record, 18 if unable to communicate
    def get_status(self, ip):
        logger.debug('Getting status of kipro %s', ip)
        try:
            r = json.loads(requests.get(f'http://{ip}/config?action=get&paramid=eParamID_TransportState', timeout=kipro_timeout_threshold).text)
            logger.debug('Status of kipro %s is %s', ip, r['value'])
            return r['value']
        except requests.exceptions.RequestException as e:
            logger.error('Error with kipro %s. \n %s', ip, e)
            return '18'

    def get_remaining_storage(self, ip):
        logger.debug('Getting remaining storage for kipro %s', ip)
        try:
            r = json.loads(requests.get(f'http://{ip}/config?action=get&paramid=eParamID_CurrentMediaAvailable', timeout=kipro_timeout_threshold).text)
            logger.debug('Remaining storage on kipro %s is %s percent.', ip, r['value'])
            return r['value']
        except requests.exceptions.RequestException as e:
            return 0

    def start_absolute(self, ip, name, include_date):
        if include_date is True:
            now = datetime.now().strftime("_%Y_%m_%d-%H_%M")
            name = f'{name}{now}'
        self.set_clip_name(ip=ip, name=name)
        self.set_rec_play_mode(ip=ip)
        self.transport_record(ip=ip)

    def toggle_start_stop(self, ip, name, include_date):
        status = self.get_status(ip=ip)
        if status == '1':
            self.start_absolute(ip=ip, name=name, include_date=include_date)
        if status == '2':
            self.transport_stop(ip=ip)

    def download_clips(self):
        root = Tk()
        root.withdraw()

        files = []

        for kipro in kipros:
            if not kipro['name'] == 'ALL':
                self.set_data_lan_mode(ip=kipro['ip'])
                r = requests.get(f"http://{kipro['ip']}/clips")
                clips = demjson.decode(r.text[:-2])
                files.append({
                    'clips': clips,
                    'ip': kipro['ip']
                })

        os.chdir(filedialog.askdirectory())

        for recorder in files:
            for clip in recorder['clips']:
                url = f"http://{recorder['ip']}/media/{clip['clipname']}"
                logger.info('Downloading clip %s from %s', clip['clipname'], url)
                wget.download(url, clip['clipname'])
        logger.info('All downloads complete')


if __name__ == '__main__':
    kipro = KiPro()
    kipro.download_clips()