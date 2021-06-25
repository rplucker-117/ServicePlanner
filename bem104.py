import requests
from logzero import logger
from bs4 import BeautifulSoup

class BEM104:
    def __init__(self, ip):
        logger.debug('BEM104 class created, ip %s', ip)
        self.ip = ip

    def switch_off(self, relay):
        logger.debug('BEM104: sending switch off, relay %s', relay)
        requests.get(f'http://{self.ip}/k0{relay}=0')

    def switch_on(self, relay):
        logger.debug('BEM104: sending switch on, relay %s', relay)
        requests.get(f'http://{self.ip}/k0{relay}=1')

    def toggle(self, relay):
        logger.debug('BEM104: sending switch toggle, relay %s', relay)
        requests.get(f'http://{self.ip}/k0{relay}=2')

    def pulse_on(self, relay):
        logger.debug('BEM104: sending pulse on, relay %s', relay)
        requests.get(f'http://{self.ip}/k0{relay}=3')

    def pulse_off(self, relay):
        logger.debug('BEM104: sending pulse off, relay %s', relay)
        requests.get(f'http://{self.ip}/k0{relay}=4')

    def pulse_toggle(self, relay):
        logger.debug('BEM104: sending switch toggle, relay %s', relay)
        requests.get(f'http://{self.ip}/k0{relay}=5')

    def get_status(self, relay):
        logger.debug('BEM104: getting status of relay %s', relay)
        r = requests.get(f'http://{self.ip}/k0{relay}=7')
        soup = BeautifulSoup(r.text, 'html.parser')
        result = int(soup.text.split()[2][0])
        logger.debug('BEM104: status of relay %s is %s', relay, result)
        return result


if __name__ == '__main__':
    b = BEM104(ip='10.1.60.90')
    b.get_status(relay=1)


