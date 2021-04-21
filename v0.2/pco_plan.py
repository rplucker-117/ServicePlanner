import requests
import json
import pprint
from settings import *
import logging


class pco_plan_update:
    logging.basicConfig(level=log_level)

    def create_app_cues(*self, service_type, plan, item_id, item_note_category_id, app_cue):
        logging.debug('received new app cue. Item id: %s, app cue: %s. Attempting creation', item_id, app_cue)

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data': {'attributes': {'content': app_cue, 'item_note_category_id': item_note_category_id}}}

        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{service_type}/plans/{plan}/items/{item_id}/item_notes/',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(APP_ID, SECRET))
        return json.loads(r.text)

    def update_app_cues(*self, service_type, plan, item_id, item_note_id, app_cue):
        logging.debug('Received new app cue. Attempting update')

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload = {'data': {'attributes': {'content': app_cue}}}

        r = requests.patch(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{service_type}/plans/{plan}/items/{item_id}/item_notes/{item_note_id}',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(APP_ID, SECRET))
        return json.loads(r.text)

    def get_item_note_id(*self, service_type, plan, item_id):
        logging.debug('Getting item note id for service type: %s, plan: %s, item_id %s.', service_type, plan, item_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{service_type}/plans/{plan}/items/{item_id}/item_notes/',
                         auth=(APP_ID, SECRET))
        logging.debug('Item request not id request made')
        ids = {}
        for iteration, data in enumerate(json.loads(r.text)['data']):
            ids.update({data['attributes']['category_name']: data['id']})
        return ids

    def check_if_item_note_exists(*self, service_type, plan, item_id, category_name):
        logging.debug('Checking if item note exists, making initial request')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{service_type}/plans/{plan}/items/{item_id}/item_notes/',
                         auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        for data in r['data']:
            if data['attributes']['category_name'] == category_name:
                logging.debug('Item note exists.')
                return True
        else:
            logging.debug('Item note does not exist')
            return False

    def create_and_update_app_cue(*self, service_type, plan, item_id, app_cue):
        logging.debug('create_and_update_app_cue: service_type: %s, plan: %s, item_id: %s, app_cue: %s', service_type, plan, item_id, app_cue)
        if pco_plan_update.check_if_item_note_exists(service_type=service_type,
                                                     plan=plan,
                                                     item_id=item_id,
                                                     category_name='App Cues'):

            item_note_id = pco_plan_update.get_item_note_id(service_type=service_type, plan=plan, item_id=item_id)
            pco_plan_update.update_app_cues(service_type=service_type,
                                            plan=plan,
                                            item_id=item_id,
                                            item_note_id=item_note_id['App Cues'],
                                            app_cue=app_cue)
        else:
            pco_plan_update.create_app_cues(service_type=service_type,
                                            plan=plan,
                                            item_id=item_id,
                                            item_note_category_id=app_cue_note_category_id,
                                            app_cue=app_cue)

    def get_item_details_from_item_id(*self, service_type, plan, item_id):
        # returns tuple of both item title(used most of the time)and all other details, used if needed
        logging.debug('get_item_details_from_item_id: service_type: %s, plan: %s, item_id: %s')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/{service_type}/plans/{plan}/items/{item_id}',
                         auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        try:
            i = data['data']['attributes']['title']
            logging.debug('successfully got details. item name: %s', i)
            return i, data
        except:
            logging.error('get_item_details_from_item_id: FAILED')