import requests

# http://10.1.60.95:49868/api/0/trigger/playlist/LowerThirds/cue/26

def cueClip(ip, playlist, clipNumber):
    requests.post(f'http://{ip}/api/0/trigger/playlist/{playlist}/cue/{clipNumber}')


# cueClip(ip='10.1.60.95', port='49868', playlist='LowerThirds', clipNumber='0')

