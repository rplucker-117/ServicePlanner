import socket

def rosstalk(rosstalk_ip, rosstalk_port, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((rosstalk_ip, rosstalk_port))
    s.send(bytes(command, 'utf-8'))
    s.send(b'\r\n')
    s.close()

