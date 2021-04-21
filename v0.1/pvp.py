import requests
import json
import pprint
from settings import *
import logging

class pvp:
    def get_pvp_data(*self, ip, port):
        r = requests.get(f'http://{ip}:{port}/api/0/data/playlists')
        data = json.loads(r.text)
        return data
    def cue_clip(*self, ip, port, playlist, clip_number):
        requests.post(f"http://{ip}:{port}/api/0/trigger/playlist/{playlist}/cue/{clip_number}")
