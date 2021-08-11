import requests
import urllib.parse
import math
from logzero import logger

class Flex:
    '''
    Possible devices: get from http://10.1.70.11:2020/devices
    Possible command names:
        -Sony Pro Bravias: power[0/1], input[1,2,3 etc]
        -QSys: value,<namedcontrol>         value (so value,LobbyMute and 1 would set LobbyMute to 1 aka “Muted” in QSys)
        http://10.1.70.11:2021/devices/sendcommand?id=A_QSys&name=value,LobbyGain&value=10
        -Lighting Scenes: scenestate[0-5], setlock[0,1]
        -Sensor iq: zonename[0,1]: 1 or 0 for power on or off (zonename is defined in the device setup)
    '''

    def __init__(self, controlflex_ip):
        self.controlflex_ip = controlflex_ip

    def send_command(self, device, commandname, value):
        r = requests.get(f'http://{self.controlflex_ip}:2021/devices/sendcommand?id={device}&name={commandname}&value={value}')
        logger.debug(f'Sent Controlflex command: {r.url}')

    def qsys_mute(self, qsys_name, qsys_zone, state): # 1 is muted, 0 is unmuted
        self.send_command(device=qsys_name, commandname=f'value,{qsys_zone}', value=state)

    def qsys_source(self, qsys_name, qsys_zone, source_number):
        self.send_command(device=qsys_name, commandname=f'value,{qsys_zone}', value=int(source_number))

    def set_qsys_volume_db(self, qsys_name, qsys_zone, db):
        self.send_command(device=qsys_name, commandname=f'value,{qsys_zone}', value=str(db))

    def set_qsys_volume_percent(self, qsys_name, qsys_zone, percent):
        db = int(percent)*1.2-100
        self.send_command(device=qsys_name, commandname=f'value,{qsys_zone}', value=math.floor(int(db)))

    def sony_pro_bravia_input(self, device_name, input_number):
        self.send_command(device=device_name, commandname='input', value=input_number)

    def sony_pro_bravia_volume(self, device_name, volume_percent):
        self.send_command(device=device_name, commandname='volume', value=volume_percent)

    def sony_pro_bravia_power(self, device_name, state):
        self.send_command(device=device_name, commandname='power', value=state)


if __name__ == '__main__':
    flex = Flex(controlflex_ip='10.1.70.11')
