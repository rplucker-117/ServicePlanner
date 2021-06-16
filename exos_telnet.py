import telnetlib
import os
import json
import pprint
import time
import logging

logging.basicConfig(level=logging.DEBUG)

class Exos():
    def __init__(self, host, user, password):

        self.user = user
        self.password = password
        self.tn = telnetlib.Telnet(host)
        self.tn.timeout(1)

        self.tn.write((self.user + '\n').encode('ascii'))
        self.tn.read_until(b'password: ').decode('ascii')

        self.tn.write((self.password + '\n').encode('ascii'))
        response = self.tn.read_until(b'# ').decode('ascii')

        self.sw_name = response.splitlines()[-1][0:-5]

    def send_command(self, command, read_until='sw_name'):
        read_until_val = self.sw_name if read_until == 'sw_name' else read_until

        logging.debug('send_command: sending command %s', command)

        self.tn.write(command.encode('ascii'))
        self.tn.write(b'\n')

        # press space a bunch for longer requests
        self.tn.write(b' ')
        self.tn.write(b' ')

        time.sleep(.1)
        response = self.tn.read_until(read_until_val.encode('ascii')).decode('ascii')

        return response

    def get_port_vlan_assignments(self, port):
        # returns the vlans (tagged and untagged) that a port is assigned to

        logging.debug('Getting port vlan assignments for port %s', port)

        vlans = {
            'untagged': [],
            'tagged': []
        }

        response = self.send_command(f'sh port {port} vlan port-number')

        logging.debug('get_port_vlan_assignments: response: %s', response)

        for line in response.splitlines()[5:-1]:
            # untagged
            untagged_char = line.find('Untagged')
            if untagged_char == -1:
                pass
            else:
                end_untagged_char = len('Untagged') + untagged_char + 2
                vlans['untagged'].append(line[end_untagged_char:])

            tagged_char = line.find('Tagged')
            if tagged_char == -1:
                pass
            else:
                end_tagged_char = len('Tagged') + tagged_char + 4
                for tagged in line[end_tagged_char:].split(', '):
                    vlans['tagged'].append(tagged)

        # If list under key untagged/tagged is empty, add None
        for s in ['untagged', 'tagged']:
            if len(vlans[s]) == 0:
                vlans[s].append(None)

        logging.debug('get_port_vlan_assignments: returning %s', vlans)

        return vlans

    def get_port_addresses(self, port):
        # Get the ip and mac address of devices attached to a port

        ips = []
        macs = []
        response = self.send_command(f'sh iparp port {port}', read_until='#')
        for line in response.splitlines()[3:]:
            if line.endswith(port):
                if line.find('Press') == -1:
                    ips.append(line.split()[1])
                    macs.append(line.split()[2])
                else:
                    ips.append(line[45:].split()[1])
                    macs.append(line[45:].split()[2])

        addresses = {
            'ips': ips,
            'macs': macs

        }
        return addresses

    def get_port_poe(self, port):
        # Get the inline power details about a specific port

        response = self.send_command(f'sh inline-power info port {port}')

        logging.debug('Getting POE info for port %s', port)
        logging.debug('poe data received: %s', response)


        try:
            data = {
                'state': response.splitlines()[5].split()[1],
                'class': response.splitlines()[5].split()[2],
                'volts': response.splitlines()[5].split()[3],
                'current': response.splitlines()[5].split()[4],
                'power': response.splitlines()[5].split()[5],
                'fault': response.splitlines()[5].split()[6]

            }
        except IndexError as e:
            logging.debug('get_port_poe: IndexError: %s', e)

            data = {
                'state': 'Not Available',
                'class': '',
                'volts': '',
                'current': '',
                'power': '',
                'fault': ''

            }

        logging.debug('get_port_poe: returning %s', data)

        return data

    def get_port_state(self, port):
        logging.debug('Getting state of port %s', port)

        response = self.send_command(f'sh port config no-refresh | grep {port}\>')

        if not len(response.splitlines()[2].split()) < 11:

            data = {
                'port_state': response.splitlines()[2].split()[2],
                'link_state': response.splitlines()[2].split()[3],
                'speed_actual': response.splitlines()[2].split()[6],
                'media': response.splitlines()[2].split()[10]
            }
        else:
            data = {
                'port_state': response.splitlines()[2].split()[2],
                'link_state': response.splitlines()[2].split()[3],
                'speed_actual': 'UNKNOWN',
                'media': 'UNKNOWN'
            }

        data['port_state'] = 'Enabled' if data['port_state'] == 'E' else data['port_state']

        if data['link_state'] == 'A':
            data['link_state'] = 'Active'
        if data['link_state'] == 'R':
            data['link_state'] = 'Ready'

        return data


    def close_connection(self):
        self.tn.close()

if __name__ == '__main__':
    ex = Exos('10.1.60.1')
    ex.get_port_state('1:6')