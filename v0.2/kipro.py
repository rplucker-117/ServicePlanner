import urllib.request
import urllib.parse
from settings import *
import json
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=log_level)

class kipro():
    def set_clip_name(*self, ip, name):
        logging.debug('Setting kipro clip name. ip: %s, name: %s', ip, name)
        payload = f'paramName=eParamID_CustomClipName&newValue={name}'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def set_rec_play_mode(*self, ip):
        logging.debug('Setting kipro %s to rec/play mode', ip)
        payload = 'paramName=eParamID_MediaState&newValue=0'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def format_current_slot(*self, ip):
        logging.debug('Formatting current slot for kipro %s', ip)
        payload = 'paramName=eParamID_FormatMedia&newValue=1'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def transport_record(*self, ip):
        logging.debug('Setting transport record on kipro %s', ip)
        payload= 'paramName=eParamID_TransportCommand&newValue=3'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def transport_stop(*self, ip):
        logging.debug('Setting transport stop on kipro %s', ip)
        payload= 'paramName=eParamID_TransportCommand&newValue=4'.encode('utf-8')
        urllib.request.urlopen(f'http://{ip}/options', data=payload)

    def get_status(*self, ip):
        logging.debug('Getting status of kipro %s', ip)
        r = json.loads(requests.get(f'http://{ip}/config?action=get&paramid=eParamID_TransportState').text)
        logging.debug('Status of kipro %s is %s', ip, r['value'])
        return r['value']

    def get_remaining_storage(*self, ip):
        logging.debug('Getting remaining storage for kipro %s', ip)
        r = json.loads(requests.get(f'http://{ip}/config?action=get&paramid=eParamID_CurrentMediaAvailable').text)
        logging.debug('Remaining storage on kipro %s is %s percent.', ip, r['value'])
        return r['value']

    def start_absolute(*self, ip, name, include_date):
        if include_date is True:
            now = datetime.now().strftime("_%Y_%m_%d-%H_%M")
            name = f'{name}{now}'
        kipro.set_clip_name(ip=ip, name=name)
        kipro.set_rec_play_mode(ip=ip)
        kipro.transport_record(ip=ip)

