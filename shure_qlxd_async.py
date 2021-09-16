import asyncio
from logzero import logger
import math

class ShureQLXD:
    def __init__(self, ip):
        self.IP_ADDR = ip
        self.PORT = 2202

        self.meter_rate = 750  # in ms. minimum 100, maximum 99999. Recommended max for this script is 2500, otherwise some functions will take a long time.
        self.meter_timeout = round(self.meter_rate / 1000) + .2


        self.reader = None
        self.writer = None

        self.is_metering = None
        self.metering_slots = [None, None, None, None]
        self.battery_levels = [None, None, None, None]

        self.__fix_meter_rate_length()

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def create_stream(self):
        self.reader, self.writer = await asyncio.open_connection(self.IP_ADDR, self.PORT)

    async def __check_if_metering(self):

        if self.reader is None:
            await self.create_stream()

        metering_slots = [False, False, False, False]

        for _ in range(1, 5):

            try:
                response = await asyncio.wait_for(
                    asyncio.gather((self.reader.readuntil(B'>')), return_exceptions=False),
                    timeout=self.meter_timeout, )

                if response[0].decode('ascii').split(' ')[1] == 'SAMPLE':
                    slot = int(response[0].decode('ascii').split(' ')[2])
                    metering_slots[slot - 1] = True

            except asyncio.TimeoutError:
                pass

        self.metering_slots = metering_slots

        return self.metering_slots

    async def __send_command(self, command):

        if self.writer is None:
            await self.create_stream()

        self.writer.write(bytes(f'< {command} >', 'ascii'))

        return

    async def __listen_for(self, str):
        # logger.debug(f'listening for {str}')

        try:
            response = await asyncio.wait_for(
                asyncio.gather((self.reader.readuntil(str.encode('ascii'))), return_exceptions=False),
                timeout=self.meter_timeout, )
            # logger.debug('__listen for found string')
            return response

        except asyncio.TimeoutError:
            # logger.debug('__Listen for timed out')
            pass

        return

    def __fix_meter_rate_length(self): # run on startup
        meter_rate_length = len(str(self.meter_rate))
        if meter_rate_length < 5:
            self.meter_rate = str(self.meter_rate)
            zeros_to_add = 5 - meter_rate_length
            for _ in range(zeros_to_add):
                self.meter_rate = '0' + self.meter_rate

    def start_metering_slot(self, slot):
        # logger.debug(f'Starting metering on slot {slot}')

        self.loop.run_until_complete(self.__send_command(f'SET {slot} METER_RATE {self.meter_rate}'))
        self.loop.run_until_complete(self.__listen_for(str=F'< REP {slot} METER_RATE {self.meter_rate} >'))

    def stop_metering_slot(self, slot):
        self.loop.run_until_complete(self.__send_command(f'SET {slot} METER_RATE 0'))
        self.loop.run_until_complete(self.__listen_for(str=F'< REP {slot} METER_RATE 00000 >'))

    def check_metering_slots(self):
        return self.loop.run_until_complete(self.__check_if_metering())

    def stop_all_metering(self):
        for i in range(1, 5):
            self.stop_metering_slot(slot=i)

    def start_all_metering(self):
        self.stop_all_metering()
        # logger.debug(f'starting all metering on device {self.IP_ADDR}')
        for i in range(1, 5):
            self.start_metering_slot(slot=i)

    def check_battery_levels(self): # stops metering on all slots, checks/returns battery levels of all slots, starts metering on slots that were previously metering
        # logger.debug(f'checking battery levels on device {self.IP_ADDR}')

        metering = self.loop.run_until_complete(self.__check_if_metering())
        self.stop_all_metering()

        battery_levels = [None, None, None, None]

        self.loop.run_until_complete(asyncio.sleep(2))

        for i in range(1, 5):
            self.loop.run_until_complete(self.__send_command(command=f'GET {i} BATT_BARS'))
            self.loop.run_until_complete(self.__listen_for('BATT_BARS '))
            response = self.loop.run_until_complete(self.__listen_for('>'))
            level = int(response[0].decode('ascii').split(' ')[0])
            battery_levels[i-1] = level

        for iteration, meter in enumerate(metering):
            if meter is True:
                self.start_metering_slot(slot=iteration+1)

        self.battery_levels = battery_levels

        return self.battery_levels

    def get_meter_info(self): # returns list of metering data a single time of
        try:
            info = [None, None, None, None]

            if None in self.metering_slots: # check what slots are being metered if check_metering_slots hasnt been run yet
                self.check_metering_slots()

            if True in self.metering_slots:
                for iteration, state in enumerate(self.metering_slots):
                    if state is True:
                        self.loop.run_until_complete(self.__listen_for(f'SAMPLE {iteration+1}'))
                        response = self.loop.run_until_complete(self.__listen_for('>'))
                        info[iteration] = {
                            'rf_level': response[0].decode('ascii').split(' ')[3],
                            'audio_level': response[0].decode('ascii').split(' ')[4]
                        }

            # logger.debug(f'Got metering info for device {self.IP_ADDR}: {info}')
        except TypeError:
            self.get_meter_info()

        return info


    def constant_return_meter_info(self): #generator
        while True:
            yield self.get_meter_info()

if __name__ == '__main__':
    qlxd = ShureQLXD('10.1.50.102')
    # qlxd.stop_all_metering()
    qlxd.start_all_metering()
    # qlxd.get_meter_info()
