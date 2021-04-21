import requests
import json
import pprint
from settings import *
import logging
from pco_plan import pco_plan_update

class pco_live:
    logging.basicConfig(level=log_level)

    def go_to_next_item(*self, service_type, plan):
        logging.debug('Going to next item plan---- service type: %s, plan: %s', service_type, plan)
        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{service_type}/plans/{plan}/live/go_to_next_item',
                      auth=(APP_ID, SECRET))
        # Look at response, if it contains errors>0>status>403, you're either not logged in or haven't taken control
        try:
            if json.loads(r.text)['errors'][0]['status'] == '403':
                logging.error("You haven't taken pco live control!")
        except KeyError:
            logging.info('Success')

    def go_to_previous_item(*self, service_type, plan):
        logging.debug('Going to previous item plan---- service type: %s, plan: %s', service_type, plan)
        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{service_type}/plans/{plan}/live/go_to_previous_item',
                      auth=(APP_ID, SECRET))
        try:
            if json.loads(r.text)['errors'][0]['status'] == '403':
                logging.error("You haven't taken pco live control!")
        except KeyError:
            logging.info('Success')

    # simply toggles control. Use in conjunction with is_controlled for more use
    def toggle_control(*self, service_type, plan):
        logging.debug('Toggling control...---- service type: %s, plan: %s', service_type, plan)
        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{service_type}/plans/{plan}/live/toggle_control',
                      auth=(APP_ID, SECRET))

        if json.loads(r.text)['data']['links']['controller'] == None:
            logging.info('You have RELEASED control')
        else:
            logging.info('You have TAKEN control')

    # get id of currently live item in pco live from service_type and plan.
    # Returns logging error and none if plan is not live.
    def get_current_live_item(*self, service_type, plan):
        logging.debug('attempting to get current live item id')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{service_type}/plans/{plan}/live/current_item_time',
                      auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        try:
            i = data['data']['relationships']['item']['data']['id']
            logging.debug('successfully got current live item id: %s', data['data']['relationships']['item']['data']['id'])
            return data['data']['relationships']['item']['data']['id']
        except KeyError:
            logging.error('Failed to get current live item id for service type %s, plan %s. Is the plan live?', service_type, plan)
            return None

    # TODO check during a live service. length and length_offset are both 0 when called when out of service time
    def get_current_live_item_time(*self, service_type, plan):
        logging.debug('getting live item time of service_type %s, plan %s', service_type, plan)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                         f'{service_type}/plans/{plan}/live/current_item_time',
                         auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        return data


    # returns boolean on if a service is being live controlled or not
    def is_controlled(*self, service_type, plan):
        logging.debug('Getting controller of live PCO service')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{service_type}/plans/{plan}/live/',
                         auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        controller = data['data']['links']['controller']

        if controller == None:
            logging.info('Current plan is NOT being live controlled')
            return False
        else:
            logging.info('Current plan IS being live controlled.')
            return True

    # looks at if a plan is being controlled, takes control if it's not. Does nothing if its already controlled
    def take_control(*self, service_type, plan):
        logging.debug('Taking live plan control...')
        if pco_live.is_controlled(service_type=service_type, plan=plan) == False:
            pco_live.toggle_control(service_type=service_type, plan=plan)
        else:
            logging.info('take_control(): Already live controller!')

    # opposite of above function
    def release_control(*self, service_type, plan):
        logging.debug('Releasing plan control...')
        if pco_live.is_controlled(service_type=service_type, plan=plan) == True:
            pco_live.toggle_control(service_type=service_type, plan=plan)
        else:
            logging.info('release_control(): Not live controller!')


    # find the next live item in service, used in pco live setting. This function is needed because headers
    # are considered items in the api, but not the live functionality. Basically this returns the next
    # item that is not a header
    def find_next_live_item(*self, service_type_id, service_id):
        items=pco_plan_update.get_service_items(service_type_id=service_type_id, service_id=service_id)[1]
        current_live_item = pco_live.get_current_live_item(service_type=service_type_id, plan=service_id)

        #find index of current live item
        for item in items:
            if item['id'] == current_live_item:
                live_item_index = item['sequence']

        def find_next_item(n):
            logging.debug('pco_live.find_next_live_item find_next_item recursive function: loop with input %s', n)
            if n > len(items):
                logging.debug('pco_live.find_next_live_item find_next_item recursive function: end of plan!')
                pass
            if not items[n]['type'] == 'header' or None:
                logging.debug('pco_live.find_next_live_item find_next_item recursive function: returning %s,'
                              'item name: %s', items[n]['id'], items[n]['title'])
                return items[n]
            else:
                return find_next_item(n+1)

        return find_next_item(live_item_index)


if __name__ == '__main__':
    print(pco_live.find_next_live_item(service_type_id=824571, service_id=51618294))