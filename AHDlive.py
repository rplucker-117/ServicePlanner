import socket
import math
import struct
import select
from logzero import logger

class AHDLive:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__establish_connection()

    def __establish_connection(self):
        self.s.connect((self.ip_address, 51325))
        logger.debug('AHDLive: Connection established: IP/Port: %s, %s', self.ip_address, 51325)

    def recall_scene(self, scene_number):
        logger.debug('AHDLive: Recalling scene %s', scene_number)

        bank = math.floor(scene_number / 128)
        scene_index = scene_number % 128

        command = b'\xbb' + struct.pack('BB', 00, 0 + bank) + b'\xcb' + struct.pack('B', scene_index - 1)
        self.s.send(command)

        select.select([self.s], [], [], .1)

    def close_connection(self):
        logger.debug('AHDLive: Closing connection')
        self.s.close()

