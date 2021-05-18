import requests
import json
import pprint
from settings import *
from logzero import logger

class pvp:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def get_pvp_data(self):
        r = requests.get(f'http://{self.ip}:{self.port}/api/0/data/playlists')
        data = json.loads(r.text)
        return data
    def cue_clip_via_index(self, playlist, clip_number):
        logger.debug('cueing pvp clip based on playlist/clip index. playlist: %s, clip index: %s', playlist, clip_number)
        requests.post(f"http://{self.ip}:{self.port}/api/0/trigger/playlist/{playlist}/cue/{clip_number}")

    def cue_clip_via_uuid(self, playlist_uuid, cue_uuid):
        logger.debug('cueing pvp clip via uuid. ip: %s, port: %s, playlist_uuid: %s, cue_uuid: %s', self.ip, self.port, playlist_uuid, cue_uuid)
        requests.post(f"http://{self.ip}:{self.port}/api/0/trigger/playlist/{playlist_uuid}/cue/{cue_uuid}")

if __name__ == '__main__':
    pvp = pvp(ip='10.1.60.95', port=49868)
    pprint.pprint(pvp.get_pvp_data())