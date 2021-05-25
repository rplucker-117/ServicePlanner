import requests
import json
import pprint
from settings import *
from logzero import logger
import zulu
from creds import Creds

creds = Creds().read()
APP_ID = creds['APP_ID']
SECRET = creds['SECRET']

class PcoPlan:
    def __init__(self, **kwargs):
        if 'service_type' in kwargs:
            self.service_type = kwargs['service_type']
        if 'plan_id' in kwargs:
            self.plan_id = kwargs['plan_id']

    def create_app_cues(self, item_id, item_note_category_id, app_cue):
        logger.debug('received new app cue. Item id: %s, app cue: %s. Attempting creation', item_id, app_cue)

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data':
                       {'attributes':
                            {'content': app_cue,
                             'item_note_category_id': item_note_category_id}
                        }
                   }

        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(APP_ID, SECRET))
        if not r.status_code == '200':
            logger.error('PcoPlan.create_app_cues FAILED: response received: %s', json.loads(r.text))
        return json.loads(r.text)

    def update_item_app_cues(self, item_id, item_note_id, app_cue):
        logger.debug('Received new app cue. Attempting update')

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data': {'attributes': {'content': app_cue}}}

        r = requests.patch(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/{item_note_id}',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(APP_ID, SECRET))
        return json.loads(r.text)

    def get_item_note_id(self, item_id):
        # returns a dict of note category: id
        logger.debug('Getting item note id for service type: %s, plan: %s, item_id %s.', self.service_type, self.plan_id, item_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/',
                         auth=(APP_ID, SECRET))
        logger.debug('Item request not id request made')
        ids = {}
        for iteration, data in enumerate(json.loads(r.text)['data']):
            ids.update({data['attributes']['category_name']: data['id']})
        return ids

    def check_if_item_note_exists(self, item_id, category_name):
        logger.debug('Checking if item note exists, making initial request')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for data in r['data']:
            if data['attributes']['category_name'] == category_name:
                logger.debug('Item note exists.')
                return True
        else:
            logger.debug('Item note does not exist')
            return False

    def create_and_update_item_app_cue(self, item_id, app_cue):
        logger.debug('create_and_update_app_cue: service_type: %s, plan: %s, item_id: %s, app_cue: %s', self.service_type, self.plan_id, item_id, app_cue)
        if self.check_if_item_note_exists(item_id=item_id, category_name='App Cues'):
            item_note_id = self.get_item_note_id(item_id=item_id)
            self.update_item_app_cues(item_id=item_id,
                                          item_note_id=item_note_id['App Cues'],
                                          app_cue=app_cue)
        else:
            try:
                self.create_app_cues(item_id=item_id,
                                         item_note_category_id=self.get_service_category_app_cue_note_category_id(),
                                         app_cue=app_cue)
            except NameError:
                logger.error('create_and_update_item_app_cue: error. Likely no app cue note category exists')

    def get_item_details_from_item_id(self, item_id):
        # returns:
        # 0: title only
        # 1: raw response, including all item details
        logger.debug('get_item_details_from_item_id: service_type: %s, plan: %s, item_id: %s', self.service_type, self.plan_id, item_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}',
                         auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        try:
            i = data['data']['attributes']['title']
            logger.debug('successfully got details. item name: %s', i)
            return i, data
        except:
            logger.error('get_item_details_from_item_id: FAILED')

    def get_plan_app_cue_note_id(self):
        # Used later for posting/updating app cues note section on each plan. This gets the id of the specific note in the selected plan
        # returns a tuple of note id along with category id
        logger.debug('Making api call to get note id for app cues in plan %s', self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        logger.debug('PcoPlan.get_plan_app_cue_note_id: response received: %s', r)
        for category in r['data']:
            logger.debug('get_plan_app_cue_note_id: checking if contains app cue')
            if category['attributes']['category_name'] == 'App Cues':
                logger.debug('Found app cue note, id %s, content: %s', category['id'], category['attributes']['content'])
                return category['id'], category['relationships']['plan_note_category']['data']['id']

    def get_plan_app_cues(self):
        # Gets content of plan app cues note, converts it to python dict
        logger.debug('PcoPlan.get_plan_app_cues called.')
        if self.check_if_plan_app_cue_exists():
            r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes',
                             auth=(APP_ID, SECRET))
            r = json.loads(r.text)
            for note in r['data']:
                if note['attributes']['category_name'] == 'App Cues':
                    logger.debug(f"PcoPlan.get_plan_app_cues: found app cue note content: {note['attributes']['content']}")
                    try:
                        return json.loads(note['attributes']['content'])
                    except json.decoder.JSONDecodeError:
                        logger.error("pco_plan.get_plan_app_cues: Found note content but it wasn't valid json. Skipping.")
                        return None
        else:
            logger.debug('PcoPlan.get_plan_app_cues: could not find note in app cues section')
            return None

    def get_plan_app_cue_note_category_id(self):
        logger.debug('get_plan_app_cue_note_category_id. Service type:  %s', self.service_type)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plan_note_categories',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for category in r['data']:
            if category['attributes']['name'] == 'App Cues':
                logger.debug('get_plan_app_cue_note_id: found app cue note category, id %s', category['id'])
                return category['id']

    def get_plan_times(self):
        # Returns list of scheduled start times of service times (no rehearsals) in dict form:
        # zulu time and human readable time, as well as plan time id
        logger.debug('get_plan_times. service_type: %s, service_id: %s', self.service_type, self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/plan_times/',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        logger.debug('get_plan_times: response received: %s',r)
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
        logger.debug('Found plan times: %s', times)
        return times

    def get_current_live_service(self):
        # Return dict of currently live plan info, none if plan is not active
        service_times = self.get_plan_times()
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/live/current_item_time/', auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for time in service_times:
            try:
                if time['id'] == r['data']['relationships']['plan_time']['data']['id']:
                    return time
            except KeyError:
                return None

    def get_service_category_app_cue_note_category_id(self):
        logger.debug('get_app_ceu_note_category_id called. service type: %s', self.service_type)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/item_note_categories',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)

        for service_type in r['data']:
            if service_type['attributes']['name'] == 'App Cues':
                logger.debug('get_service_cateogry_app_cue_note_category_id: found id: %s', service_type['id'])
                return service_type['id']

    def get_plan_note_content(self, note_id):
        # get content of a plan note (different from item note)
        logger.debug('Getting plan note content for plan %s, note id %s', self.plan_id, note_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{note_id}',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        try:
            return json.loads(r['data']['attributes']['content'])
        except:
            logger.error('pco_plan_update.get_plan_note_content: No note exists for service_type: %s, plan: %s, note_id: %s',
                          self.service_type, self.plan_id, note_id)
            return None

    def create_plan_app_cue(self, note_content):
        #  post app cue to plan notes ONLY if it doesn't already exist
        logger.debug('Attempting to create plan app cue')
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
        logger.debug('check_if_plan_app_cue_exists: service type: %s, plan: %s', self.service_type, self.plan_id)

        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for note in r['data']:
            if note['attributes']['category_name'] == 'App Cues': #check if there's content in note
                logger.debug('check_if_plan_app_cue_note_exists: found plan note with category_name of "App Cues". Content: %s', note['attributes']['content'])
                try:
                    json.loads(note['attributes']['content']) #see if content is valid json
                    logger.debug('PcoPlan.check_if_plan_app_cue_exists: valid json found, returning True')
                    return True # return true if valid json
                except Exception as e:
                    logger.error('Found note content in plan app cues section, but it was not valid json. Skipping and removing content from PCO note.')
                    self.remove_plan_app_cues()
                    return False # return false if not valid json
            else:
                logger.debug('check_if_plan_app_cue_note_exists: did not find plan note with category_name of "App Cues."')
                return False
        if len(r['data']) == 0:
            return False

    def remove_plan_app_cues(self): # removes all content on "app cue" plan note section
        logger.debug('PcoPlan.remove_plan_app_cue called')
        note_ids = self.get_plan_app_cue_note_id()
        if note_ids is not None:
            for note in note_ids:
                logger.debug('removing plan app cue note with id %s', note)
                requests.delete(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{note}',
                                auth=(APP_ID, SECRET))
        else:
            logger.error('PcoPlan.remove_plan_app_cues: no plan app cue notes were found!')

    def update_plan_app_cue(self, note_content):
        # update content of plan app cue note section ONLY if it already exists
        logger.debug('Updating plan app cues, plan id: %s, content: %s', self.plan_id, note_content)
        app_cue_note_id = self.get_plan_app_cue_note_id()[0]
        logger.debug('Update_plan_app_cue: app_cue_note_id is %s', app_cue_note_id[0])

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data': {'attributes': {'content': note_content}}}

        r = requests.patch(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{app_cue_note_id}',
                           headers=request_headers,
                           data=json.dumps(payload),
                           auth=(APP_ID, SECRET))
        r = json.loads(r.text)

        if r['data']['attributes']['content'] == note_content:
            logger.debug('update_plan_app_cue: success on adding %s to app_cue note category', note_content)
        else:
            logger.error('update_plan_app_cue: error on adding %s', note_content)

    def create_and_update_plan_app_cues(self, note_content):
        does_exist = self.check_if_plan_app_cue_exists()
        if does_exist:
            self.update_plan_app_cue(note_content=note_content)
        if not does_exist:
            self.create_plan_app_cue(note_content=note_content)

    def get_service_types(self):
        # Gets services types from root level. Returns:
        # 0: raw response data in python dict form
        # 1: list of dicts of name / id
        logger.debug('get_service_types called')
        top_request = requests.get('https://api.planningcenteronline.com/services/v2/service_types/', auth=(APP_ID, SECRET))
        top_request_dict = json.loads(top_request.text)

        service_types = []
        for service_type in top_request_dict['data']:
            service_types.append({
                'name': service_type['attributes']['name'],
                'id': service_type['id']
            })

        return top_request_dict, service_types

    def get_services_from_service_type(self, **offset):
        # Gets services within a service type id. Offset is how many plans it returns,
        # starting from the most far in advance one, with a max of 25.
        # First makes request to get total number of plans, then sets offset based on total_count - offset
        # returns both:
        # 0: raw response data in python dict form
        # 1: list of dict of series_title / title / date / id
        if offset == {}:
            logger.debug('get_services_from_service_type: Offset not specified! Using default 10.')
            offset = 10
        elif offset is None:
            offset = 10
        # print(offset)

        logger.debug('get_services_from_service_type: Making call to get total number of services in service type.')
        total_items_request = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{self.service_type}/plans',
                                           auth=(APP_ID, SECRET))

        total_items_in_service_type = int(json.loads(total_items_request.text)['meta']['total_count'])
        offset = total_items_in_service_type - offset

        logger.debug('get_services_from_service_type: getting services from, service type id: %s, offset: %s', self.service_type, offset)
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

    def get_service_items(self):
        # Gets service items given a service type id and service id. Returns:
        # 0: raw response data in python dict form
        # 1: list of dicts containing item title / type / length / service position / id / sequence, as well as applicable notes
        logger.debug('pco_plan_update.get_service_items called. service_type_id: %s, service_id: %s', self.service_type, self.plan_id)

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
                        logger.debug('pco_plan.get_service_items: content: %s', note_content)
                        note_content = json.loads(note_content)

                    item['notes'][dict_key] = note_content

        logger.debug('pco_plan_upadte: received service items. %s', service_items)

        return service_request_dict, service_items

    def get_service_type_details_from_id(self):
        # returns:
        # 0: raw response data in dict form
        # 1: plan type name
        logger.debug('pco_plan_update.get_service_type_details_from_id: id %s', self.service_type)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                                       f'{self.service_type}', auth=(APP_ID, SECRET))
        data = json.loads(r.text)

        return data, data['data']['attributes']['name']

    def get_service_details_from_id(self):
        # returns details about a specific service, without items:
        # 0: raw response data in dict form
        # 1: dict of dates, series_title, title
        logger.debug('pco_plan_update.get_service_details_from_id: service_type_id: %s, service_id: %s',
                      self.service_type, self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                         f'{self.service_type}/plans/{self.plan_id}', auth=(APP_ID, SECRET))
        data = json.loads(r.text)

        service_details = {
            'date': data['data']['attributes']['dates'],
            'series_title': data['data']['attributes']['series_title'],
            'title': data['data']['attributes']['title']
        }
        logger.debug('pco_plan_update.get_service_details_from_id: date: %s, series_title: %s, title: %s',
                      service_details['date'], service_details['series_title'], service_details['title'])
        return data, service_details

    def get_assigned_people(self):
        # return list of dicts of all people assigned to plan. Dict includes name, position name, and accept status
        logger.debug('PcoPlan.get_assigned_people: Getting people assigned to plan id %s', self.plan_id)

        r = requests.get(f"https://api.planningcenteronline.com/services/v2/service_types/"
                         f"{self.service_type}/plans/{self.plan_id}/team_members", auth=(APP_ID, SECRET))
        r = json.loads(r.text)

        team_members = []

        for person in r['data']:
            team_members.append({
                'name': person['attributes']['name'],
                'position': person['attributes']['team_position_name'],
                'status': person['attributes']['status']
            })

        return team_members

if __name__ == '__main__':
    plan = PcoPlan(service_type=1039564, plan_id=52356777)
    plan.remove_plan_app_cues()

