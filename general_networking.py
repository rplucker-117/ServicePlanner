import subprocess
import socket
import re


def is_host_online(hostname: str, timeout: float=1) -> bool:
    """
    Determines if a network host is online or not.
    :param hostname: ipv4 or ipv6 address. fqdn will not work.
    :return: bool of result
    """

    try:
        command = subprocess.run(['ping', '-n', timeout, hostname], check=True, capture_output=True)
    except subprocess.CalledProcessError:  # process returned non-0 exit code.
        return False
    response_str = command.stdout.decode('utf-8')

    if f'Reply from {hostname}' in response_str:
        return True
    else:
        return False


def is_local_port_in_use(port: int) -> bool:
    """
    Determines if a network port is in use and not able to be used (open) or not (closed) on 0.0.0.0.
    :param port: Port to test
    :return: bool of result. True if the port is in use, False if the port is open.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)

    try:
        sock.bind(('0.0.0.0', port))
    except socket.error:
        return True
    else:
        sock.close()
        return False


def is_remote_port_bindable(ip: str, port: int) -> bool:
    """
    Determines if a remote port is able to be connected to (True), or not (False)
    :param ip: IP of device or fqdn
    :param port: Port to test
    :return: bool of result. True if port is able to be connected to, false if not
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((ip, port))
        sock.shutdown(1)
        return True
    except:
        return False

def is_mac_address_valid(mac: str) -> bool:
    """
    Determines if mac address format is valid or not
    :param mac: mac address
    :return: bool of result
    """

    return True if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()) else False

if __name__ == '__main__':
    print(is_remote_port_bindable('10.1.60.11', 7788))
