import requests
from logzero import logger
import pprint


class AJAKumo:
    def __init__(self, ip):
        self.ip_address = ip
        self.num_source = int(self.get_number_of_sources())
        self.num_dest = int(self.get_number_of_destinations())

    def get_number_of_sources(self):
        r = requests.get(f'http://{self.ip_address}/config?action=get&paramid=eParamID_NumberOfSources').json()
        sources = r['value']

        return sources

    def get_number_of_destinations(self):
        r = requests.get(f'http://{self.ip_address}/config?action=get&paramid=eParamID_NumberOfDestinations').json()
        dest = r['value']

        return dest

    def get_source_name(self, source_num):
        line1_json = requests.get(f'http://{self.ip_address}/config?action=get&paramid=eParamID_XPT_Source{source_num}_Line_1').json()
        line2_json = requests.get(f'http://{self.ip_address}/config?action=get&paramid=eParamID_XPT_Source{source_num}_Line_2').json()

        if line2_json['value'] != '':
            return f'{line1_json["value"]} {line2_json["value"]}'
        if line1_json['value'] == '' and line2_json['value'] == '':
            return None
        else:
            return f'{line1_json["value"]}'

    def get_all_source_names(self):
        source_names = []
        for source in range(1, self.num_source+1):
            source_names.append(self.get_source_name(source_num=source))

        return source_names

    def get_dest_name(self, dest_num):
        line1_json = requests.get(f'http://{self.ip_address}/config?action=get&paramid=eParamID_XPT_Destination{dest_num}_Line_1').json()
        line2_json = requests.get(f'http://{self.ip_address}/config?action=get&paramid=eParamID_XPT_Destination{dest_num}_Line_2').json()

        if line2_json['value'] != '':
            return f'{line1_json["value"]} {line2_json["value"]}'
        if line1_json['value'] == '' and line2_json['value'] == '':
            return None
        else:
            return f'{line1_json["value"]}'

    def get_all_dest_names(self):
        dest_names = []
        for dest in range(1, self.num_dest+1):
            dest_names.append(self.get_dest_name(dest_num=dest))

        return dest_names

    def get_route_from_dest(self, dest_num):
        r = requests.get(f'http://{self.ip_address}/config?action=get&paramid=eParamID_XPT_Destination{dest_num}_Status').json()
        return int(r['value'])

    def route_source_to_dest(self, source_num, dest_num):
        r = requests.get(f'http://{self.ip_address}/config?action=set&paramid=eParamID_XPT_Destination{dest_num}_Status&value={source_num}').json()
        return int(r['value'])

if __name__ == '__main__':
    kumo = AJAKumo(ip='10.1.60.12')
    pprint.pprint(kumo.get_all_dest_names())

