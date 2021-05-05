import requests
import json
import pprint
from settings import *
import logging

class pvp:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def get_pvp_data(self):
        r = requests.get(f'http://{self.ip}:{self.port}/api/0/data/playlists')
        data = json.loads(r.text)
        return data
    def cue_clip(self, playlist, clip_number):
        requests.post(f"http://{self.ip}:{self.port}/api/0/trigger/playlist/{playlist}/cue/{clip_number}")
