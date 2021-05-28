import requests
import json
import urllib.parse
from logzero import logger

class EZOutlet2:
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

    def turn_off(self):
        self.__make_request(control=0)

    def turn_on(self):
        self.__make_request(control=1)

    def toggle_state(self):
        self.__make_request(control=2)

    def reset(self):
        self.__make_request(control=3)

    def __make_request(self, control):  # control parameters: 0: off, 1: on, 2: toggle state, 3: reset
        logger.debug('EZOutlet2: make request with control param %s, ip: %s', control, self.ip)

        request_content = {
            'user': self.user,
            'passwd': self.password,
            'target': 1,
            'control': control
        }

        request_content_encoded = urllib.parse.urlencode(request_content)
        r = requests.get(f'http://{self.ip}/cgi-bin/control2.cgi?{request_content_encoded}')

        if r.status_code == 200:
            logger.debug('EZOutlet2: request made successfully. control param: %s, ip: %s', control, self.ip)
        else:
            logger.error('EZOutlet2: request returned error. Control param %s, ip %s, response body: %s \n request: %s', control, self.ip, r.text, r.raw)




if __name__ == '__main__':
    outlet = EZOutlet2(ip='10.1.60.96', user='admin', password='admin')
    outlet.turn_on()