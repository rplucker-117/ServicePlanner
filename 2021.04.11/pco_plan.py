import requests
import json
import pprint
from settings import *
import logging
import zulu


class PcoPlan:
    def __init__(self, **kwargs):
        if 'service_type' in kwargs:
            self.service_type = kwargs['service_type']
        if 'plan_id' in kwargs:
            self.plan_id = kwargs['plan_id']

    logging.basicConfig(level=log_level)

    def create_app_cues(self, item_id, item_note_category_id, app_cue):
        logging.debug('received new app cue. Item id: %s, app cue: %s. Attempting creation', item_id, app_cue)

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data': {'attributes': {'content': app_cue, 'item_note_category_id': item_note_category_id}}}

        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(APP_ID, SECRET))
        return json.loads(r.text)

    def update_item_app_cues(self, item_id, item_note_id, app_cue):
        logging.debug('Received new app cue. Attempting update')

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data': {'attributes': {'content': app_cue}}}

        r = requests.patch(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/{item_note_id}',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(APP_ID, SECRET))
        return json.loads(r.text)
    # returns a dict of note category: id
    def get_item_note_id(self, item_id):
        logging.debug('Getting item note id for service type: %s, plan: %s, item_id %s.', self.service_type, self.plan_id, item_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/',
                         auth=(APP_ID, SECRET))
        logging.debug('Item request not id request made')
        ids = {}
        for iteration, data in enumerate(json.loads(r.text)['data']):
            ids.update({data['attributes']['category_name']: data['id']})
        return ids

    def check_if_item_note_exists(self, item_id, category_name):
        logging.debug('Checking if item note exists, making initial request')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for data in r['data']:
            if data['attributes']['category_name'] == category_name:
                logging.debug('Item note exists.')
                return True
        else:
            logging.debug('Item note does not exist')
            return False

    def create_and_update_item_app_cue(self, item_id, app_cue):
        logging.debug('create_and_update_app_cue: service_type: %s, plan: %s, item_id: %s, app_cue: %s', self.service_type, self.plan_id, item_id, app_cue)
        if self.check_if_item_note_exists(item_id=item_id, category_name='App Cues'):
            item_note_id = self.get_item_note_id(item_id=item_id)
            self.update_item_app_cues(item_id=item_id,
                                          item_note_id=item_note_id['App Cues'],
                                          app_cue=app_cue)
        else:
            self.create_app_cues(item_id=item_id,
                                     item_note_category_id=app_cue_note_category_id,
                                     app_cue=app_cue)

    def get_item_details_from_item_id(self, item_id):
        # returns:
        # 0: title only
        # 1: raw response, including all item details
        logging.debug('get_item_details_from_item_id: service_type: %s, plan: %s, item_id: %s', self.service_type, self.plan_id, item_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}',
                         auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        try:
            i = data['data']['attributes']['title']
            logging.debug('successfully got details. item name: %s', i)
            return i, data
        except:
            logging.error('get_item_details_from_item_id: FAILED')

    # Used later for posting/updating app cues note section on each plan. This gets the id of the specific note in the selected plan
    # returns a tuple of note id along with category id
    def get_plan_app_cue_note_id(self):
        logging.debug('Making api call to get note id for app cues in plan %s', self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for category in r['data']:
            logging.debug('get_plan_app_cue_note_id: checking if contains app cue')
            if category['attributes']['category_name'] == 'App Cues':
                logging.debug('Found app cue note, id %s, content: %s', category['id'], category['attributes']['content'])
                return category['id'], category['relationships']['plan_note_category']['data']['id']

    def get_plan_app_cue_note_category_id(self):
        logging.debug('get_plan_app_cue_note_category_id. Service type:  %s', self.service_type)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plan_note_categories',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for category in r['data']:
            if category['attributes']['name'] == 'App Cues':
                logging.debug('get_plan_app_cue_note_id: found app cue note category, id %s', category['id'])
                return category['id']

    # Returns list of scheduled start times of service times (no rehearsals) in dict form:
    # zulu time and human readable time, as well as plan time id
    def get_plan_times(self):
        logging.debug('get_plan_times. service_type: %s, service_id: %s', self.service_type, self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/plan_times/',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        logging.debug('%s get_plan_times: response received: %s %s', '\n\n', r, '\n')
        times = []
        for service_time in r['data']:
            if not service_time['attributes']['time_type'] == 'rehearsal':
                z = service_time['attributes']['starts_at']
                local = zulu.parse(z).format('%Y-%m-%d  %H:%M', tz='local')
                times.append({
                    'z': z,
                    'local': local,
                    'id': service_time['id']
                })
        logging.debug('Found plan times: %s', times)
        return times

    def get_service_cateogry_app_cue_note_category_id(self):
        logging.debug('get_app_ceu_note_category_id called. service type: %s', self.service_type)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/item_note_categories',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)

        for service_type in r['data']:
            if service_type['attributes']['name'] == 'App Cues':
                logging.debug('get_service_cateogry_app_cue_note_category_id: found id: %s', service_type['id'])
                return service_type['id']

    # get content of a plan note (different from item note)
    def get_plan_note_content(self, note_id):
        logging.debug('Getting plan note content for plan %s, note id %s', self.plan_id, note_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{note_id}',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        try:
            return json.loads(r['data']['attributes']['content'])
        except:
            logging.error('pco_plan_update.get_plan_note_content: No note exists for service_type: %s, plan: %s, note_id: %s',
                          self.service_type, self.plan_id, note_id)
            return None

    #  post app cue to plan notes ONLY if it doesn't already exist
    def create_plan_app_cue(self, note_content):
        logging.debug('Attempting to create plan app cue')
        app_cue_note_category_id = self.get_plan_app_cue_note_category_id()

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {
                      "data": {
                        "type": "PlanNote",
                        "attributes": {
                          "content": note_content,
                          "plan_note_category_id": app_cue_note_category_id
                        },
                      }
                    }
        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(APP_ID, SECRET))

    def check_if_plan_app_cue_exists(self):
        logging.debug('check_if_plan_app_cue_exists: service type: %s, plan: %s', self.service_type, self.plan_id)

        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for note in r['data']:
            if note['attributes']['category_name'] == 'App Cues':
                logging.debug('check_if_plan_app_cue_note_exists: found plan note with category_name of "App Cues". Content: %s', note['attributes']['content'])
                return True
            else:
                logging.debug('check_if_plan_app_cue_note_exists: did not find plan note with category_name of "App Cues."')
                return False

    # update content of plan app cue note section ONLY if it already exists
    def update_plan_app_cue(self, note_content):
        logging.debug('Updating plan app cues, plan id: %s, content: %s', self.plan_id, note_content)
        app_cue_note_id = self.get_plan_app_cue_note_id()[0]
        logging.debug('Update_plan_app_cue: app_cue_note_id is %s', app_cue_note_id[0])

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data': {'attributes': {'content': note_content}}}

        r = requests.patch(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{app_cue_note_id}',
                           headers=request_headers,
                           data=json.dumps(payload),
                           auth=(APP_ID, SECRET))
        r = json.loads(r.text)

        if r['data']['attributes']['content'] == note_content:
            logging.debug('update_plan_app_cue: success on adding %s to app_cue note category', note_content)
        else:
            logging.error('update_plan_app_cue: error on adding %s', note_content)

    # Gets services types from root level. Returns:
    # 0: raw response data in python dict form
    # 1: list of dicts of name / id
    def get_service_types(self):
        logging.debug('get_service_types called')
        top_request = requests.get('https://api.planningcenteronline.com/services/v2/service_types/', auth=(APP_ID, SECRET))
        top_request_dict = json.loads(top_request.text)

        service_types = []
        for service_type in top_request_dict['data']:
            service_types.append({
                'name': service_type['attributes']['name'],
                'id': service_type['id']
            })

        return top_request_dict, service_types

    # Gets services within a service type id. Offset is how many plans it returns,
    # starting from the most far in advance one, with a max of 25.
    # First makes request to get total number of plans, then sets offset based on total_count - offset
    # returns both:
    # 0: raw response data in python dict form
    # 1: list of dict of series_title / title / date / id
    def get_services_from_service_type(self, **offset):
        if offset == {}:
            logging.debug('get_services_from_service_type: Offset not specified! Using default 10.')
            offset = 10
        elif offset is None:
            offset = 10
        # print(offset)

        logging.debug('get_services_from_service_type: Making call to get total number of services in service type.')
        total_items_request = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans',
                                           auth=(APP_ID, SECRET))

        total_items_in_service_type = int(json.loads(total_items_request.text)['meta']['total_count'])
        offset = total_items_in_service_type - offset

        logging.debug('get_services_from_service_type: getting services from, service type id: %s, offset: %s', self.service_type, offset)
        services_request = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans'
                                   f'?&filter=&offset={offset}', auth=(APP_ID, SECRET))
        services_request_dict = json.loads(services_request.text)

        services = []
        for service in services_request_dict['data']:
            services.append({
                'title': service['attributes']['title'],
                'series_title': service['attributes']['series_title'],
                'date': service['attributes']['dates'],
                'id': service['id']
            })

        return services_request_dict, services

    # Gets service items given a service type id and service id. Returns:
    # 0: raw response data in python dict form
    # 1: list of dicts containing item title / type / length / service position / id / sequence, as well as applicable notes
    def get_service_items(self):
        logging.debug('pco_plan_update.get_service_items called. service_type_id: %s, service_id: %s', self.service_type, self.plan_id)

        service_request = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                                       f'{self.service_type}/plans/{self.plan_id}/items?&include=item_notes', auth=(APP_ID, SECRET))
        service_request_dict = json.loads(service_request.text)

        # load response data into dict
        service_items = []
        for service_item in service_request_dict['data']:
                service_items.append({
                    'title': service_item['attributes']['title'],
                    'type': service_item['attributes']['item_type'],
                    'length': service_item['attributes']['length'],
                    'service_position': service_item['attributes']['service_position'],
                    'id': service_item['id'],
                    'sequence': service_item['attributes']['sequence'],
                    'notes': {}
                })
        # initial request also includes all item notes, but in a separate dict. Loop through every note returned in ['included'],
        # if item id matches the current dict loop item id, add its content to the 'notes' dict. If note category name is 'App Cues',
        # convert it from json to python dict
        for note in service_request_dict['included']:
            item_id = note['relationships']['item']['data']['id']
            for item in service_items:
                if item['id'] == item_id:
                    dict_key = note['attributes']['category_name']
                    note_content = note['attributes']['content']

                    if dict_key == 'App Cues':
                        note_content = json.loads(note_content)

                    item['notes'][dict_key] = note_content

        logging.debug('pco_plan_upadte: received service items. %s', service_items)

        return service_request_dict, service_items

    # returns:
    # 0: raw response data in dict form
    # 1: plan type name
    def get_service_type_details_from_id(self):
        logging.debug('pco_plan_update.get_service_type_details_from_id: id %s', self.service_type)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                                       f'{self.service_type}', auth=(APP_ID, SECRET))
        data = json.loads(r.text)

        return data, data['data']['attributes']['name']

    # returns details about a specific service, without items:
    # 0: raw response data in dict form
    # 1: dict of dates, series_title, title
    def get_service_details_from_id(self):
        logging.debug('pco_plan_update.get_service_details_from_id: service_type_id: %s, service_id: %s',
                      self.service_type, self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                         f'{self.service_type}/plans/{self.plan_id}', auth=(APP_ID, SECRET))
        data = json.loads(r.text)

        service_details = {
            'date': data['data']['attributes']['dates'],
            'series_title': data['data']['attributes']['series_title'],
            'title': data['data']['attributes']['title']
        }
        logging.debug('pco_plan_update.get_service_details_from_id: date: %s, series_title: %s, title: %s',
                      service_details['date'], service_details['series_title'], service_details['title'])
        return data, service_details

    def get_live_info(self):
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/live/current_item_time/', auth=(APP_ID, SECRET))
        pprint.pprint(json.loads(r.text))



if __name__ == '__main__':
    plan = PcoPlan(service_type=824571, plan_id=52371712)
    pprint.pprint(plan.get_service_items())

