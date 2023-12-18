import asyncio
from logzero import logger
import pprint
import threading
import time
import concurrent.futures._base
import logging

logging.getLogger('asyncio').setLevel(logging.CRITICAL)

class ShureQLXD:
    def __init__(self, ip):
        self.IP_ADDR = ip
        self.PORT = 2202

        self.meter_rate = 1000
        self.set_meter_rate()


        self.reader = None
        self.writer = None

        self.loop = asyncio.new_event_loop()
        self.set_event_loop()

        self.loop.run_until_complete(self.create_stream())

        self.device_id = None
        self.channel_names = [None, None, None, None]
        self.battery_levels = [None, None, None, None]
        self.rf_levels = [None, None, None, None]
        self.audio_levels = [None, None, None, None]

        self.has_started = False
        self.is_metering = False


    async def create_stream(self):
        self.reader, self.writer = await asyncio.open_connection(self.IP_ADDR, self.PORT)

    def set_event_loop(self):
        logger.debug('shure_qlxd_async: setting event loop: ip: %s', self.IP_ADDR)
        asyncio.set_event_loop(self.loop)

    async def __send_command(self, command):
        # logger.debug('sending command to device %s %s', self.IP_ADDR, command)

        self.writer.write(bytes(f'< {command} >', 'ascii'))
        return

    async def __listen_for(self, str, timeout=.5):
        # logger.debug(f'listening for {str}')
        try:
            response = await asyncio.wait_for(
                asyncio.gather((self.reader.readuntil(str.encode('ascii')))),
                timeout=timeout, )
            # logger.debug('__listen for found string: %s', response)
            return response[0].decode('ascii')

        except asyncio.TimeoutError or asyncio.CancelledError or concurrent.futures._base.CancelledError:
            logger.warning('__Listen for timed out on ip %s: %s', self.IP_ADDR, str)
            raise TimeoutError

    def __parse_response(self, response):
        # logger.debug('parsing %s', response)
        response_split = response.split(' ')

        # the below functions update class variables only

        def set_device_id():
            self.device_id = response.split('{')[1].split('}')[0]
            return self.device_id

        def set_channel_name():
            name = response.split('{')[1].split('}')[0]
            self.channel_names[int(response_split[2])-1] = name
            return self.channel_names

        def set_channel_rf():
            level = response_split[4]
            self.rf_levels[int(response_split[2])-1] = level
            return self.rf_levels

        def set_channel_audio():
            level = response_split[4]
            self.audio_levels[int(response_split[2])-1] = level
            return self.audio_levels

        def set_channel_battery():
            level = response_split[4]
            self.battery_levels[int(response_split[2])-1] = level
            return self.battery_levels

        def parse(argument, type): # all responses are passed to this
            # logger.debug('parsing response, %s', response_split)
            device_params = {
                'DEVICE_ID': set_device_id
            }

            channel_params = {
                'CHAN_NAME': set_channel_name,
                'RX_RF_LVL': set_channel_rf,
                'AUDIO_LVL': set_channel_audio,
                'BATT_BARS': set_channel_battery
            }

            if type == 'device':
                try:
                    device_params.get(argument)()
                except:
                    pass

            if type == 'channel':
                try:
                    channel_params.get(argument)()
                except:
                    pass

            if type == 'channel_sample_all': # this is run if response type is like '< SAMPLE X ALL X 000 000 >'. Different from channel because response is for name/rf/audio/batt_bars individually
                self.rf_levels[int(response_split[2])-1] = int(response_split[5])
                self.audio_levels[int(response_split[2])-1] = int(response_split[6])

            return

        try:
            int(response_split[2])
            if response_split[1] == 'REP':
                parse(argument=response_split[3], type='channel')
            elif response_split[1] == 'SAMPLE':
                parse(argument=response_split[3], type='channel_sample_all')
        except ValueError:
            parse(argument=response_split[2], type='device')

    def __get_main_info(self):
        def listen():
            try:
                response = self.loop.run_until_complete(self.__listen_for('>'))
                self.__parse_response(response)
                if not response.split()[3] == 'ENCRYPTION_WARNING':
                    listen()

            except TimeoutError:
                pass
        listen()

    def continuous_meter(self): # generator that continuously returns rf, audio, and battery levels
        if not self.has_started:
            self.get_all()
            self.has_started = True

        if not self.is_metering:
            self.start_all_metering()

        while True:
            self.__parse_response(self.loop.run_until_complete(self.__listen_for('>', timeout=None)))

            yield [
                {'rf': self.rf_levels[0], 'aud': self.audio_levels[0], 'bat': self.battery_levels[0]},
                {'rf': self.rf_levels[1], 'aud': self.audio_levels[1], 'bat': self.battery_levels[1]},
                {'rf': self.rf_levels[2], 'aud': self.audio_levels[2], 'bat': self.battery_levels[2]},
                {'rf': self.rf_levels[3], 'aud': self.audio_levels[3], 'bat': self.battery_levels[3]},
            ]


    def set_meter_rate(self, rate=1000):
        self.meter_rate = rate

        def fix():
            if len(str(self.meter_rate)) < 5:
                self.meter_rate = '0' + str(self.meter_rate)
                fix()

        fix()

        return self.meter_rate

    def stop_all_metering(self):
        for i in range(1, 5):
            self.loop.run_until_complete(self.__send_command(f'SET {i} METER_RATE 0'))
            self.loop.run_until_complete(self.__listen_for(f'REP {i} METER_RATE 00000 >'))
        self.is_metering = False


    def start_all_metering(self):
        for i in range(1, 5):
            self.loop.run_until_complete(self.__send_command(f'SET {i} METER_RATE {self.meter_rate}'))
            self.loop.run_until_complete(self.__listen_for(f'REP {i} METER_RATE {self.meter_rate} >'))
        self.is_metering = True

    def get_all(self): # gets device name, channel names, rf level, audio level, battery level, update class variables
        logger.debug('Getting all info for QLXD Receiver %s', self.IP_ADDR)
        for i in range(1, 5):
            logger.debug('Getting info for QLXD channel %s on device %s', i, self.IP_ADDR)
            self.loop.run_until_complete(self.__send_command(command=f'GET {i} ALL'))
            self.__get_main_info()
        logger.debug('Got all info for QLXD receiver %s', self.IP_ADDR)

    def check_if_metering(self):
        try:
            self.loop.run_until_complete(self.__listen_for('SAMPLE', timeout=(self.meter_rate/1000+.2)))
            return True
        except TimeoutError:
            return False


    def startup(self):
        self.get_all()
        self.has_started = True



if __name__ == '__main__':
    qlxd = ShureQLXD(ip='10.1.50.101')
    # for meter in qlxd.continuous_meter():
    #     pprint.pprint(meter)
    qlxd.stop_all_metering()
    # qlxd.get_all()