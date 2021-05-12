import socket
from logzero import logger
import time

class ScpaViaIP2SL:
    def __init__(self, ip, port=4999):
        self.ip = ip
        self.port = port
        self.socket = None

    def __create_socket(self):
        logger.debug('Opening new socket')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(.5)

    def __connect(self):
        try:
            self.socket.connect((self.ip, self.port))
            logger.debug('socket connected')
        except socket.timeout:
            logger.error('IP2SL did not respond. Do you have the right host address?')

    def __listen(self):
        response = []
        while True:
            try:
                response.append(self.socket.recv(64).decode('ascii'))
            except socket.timeout:
                break
        logger.debug('received response: %s', response)
        return response

    def __close(self):
        logger.debug('Closing socket')
        self.socket.close()

    def __send_data(self, data, cr=True):
        # data = '\r' + data + '\r' if cr else data
        data = data.encode('ascii')

        try:
            self.socket.sendall(data)
            if cr:
                self.socket.sendall('\r\n'.encode('ascii'))
        except socket.timeout:
            logger.error('IP2SL did not respond. Do you have the right host address?')

    def get_status(self, output, recursive=False):
        time.sleep(2)
        self.__create_socket()
        self.__connect()

        if not recursive:
            output -= 1
        else:
            time.sleep(3.5)

        for _ in range(3 - len(str(output))):
            output = '0' + str(output)
        command = 'R' + str(output)

        self.__send_data(data=command)

        for r in self.__listen():
            for l in r.split('\r'):
                for i in l.splitlines():
                    if len(i.split(',')) == 8:
                        response = i.split(',')[0]
        self.__close()

        try:
            return response
        except UnboundLocalError:
            logger.warning('Did not receive a valid response. Retrying.')
            return self.get_status(output=output, recursive=True)

    def switch_output(self, input, output, breakaway=1):
        input -= 1
        for _ in range(3 - len(str(input))):
            input = '0' + str(input)
        input_str = input

        output -= 1
        for _ in range(3 - len(str(output))):
            output = '0' + str(output)
        output_str = output

        command = 'X' + output_str + ',' + input_str + ',' + str(breakaway)

        self.__connect()
        self.__send_data(data=command)
        self.__close()

if __name__ == '__main__':
    scp = ScpaViaIP2SL(ip='10.1.60.128')
    while True:
        scp.get_status(output=5)