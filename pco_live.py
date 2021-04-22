import requests
import json
import pprint
from settings import *
from logzero import logger
from pco_plan import PcoPlan
import time
from creds import Creds

creds = Creds().read()
APP_ID = creds['APP_ID']
SECRET = creds['SECRET']

class PcoLive:
    def __init__(self, service_type_id, plan_id):
        self.service_type_id = service_type_id
        self.plan_id = plan_id

        self.pco_plan = PcoPlan(service_type=service_type_id, plan_id=plan_id)

    # logger.basicConfig(level=log_level)

    def go_to_next_item(self):
        logger.debug('Going to next item plan---- service type: %s, plan: %s', self.service_type_id, self.plan_id)
        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type_id}/plans/{self.plan_id}/live/go_to_next_item',
                      auth=(APP_ID, SECRET))
        # Look at response, if it contains errors>0>status>403, you're either not logged in or haven't taken control
        try:
            if json.loads(r.text)['errors'][0]['status'] == '403':
                logger.error("You haven't taken pco live control!")
        except KeyError:
            logger.info('go_to_next_item: success')

    def go_to_previous_item(self):
        logger.debug('Going to previous item plan---- service type: %s, plan: %s', self.service_type_id, self.plan_id)
        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type_id}/plans/{self.plan_id}/live/go_to_previous_item',
                      auth=(APP_ID, SECRET))
        try:
            if json.loads(r.text)['errors'][0]['status'] == '403':
                logger.error("You haven't taken pco live control!")
        except KeyError:
            logger.info('go_to_previous_item: success')

    # simply toggles control. Use in conjunction with is_controlled for more use
    def toggle_control(self):
        logger.debug('Toggling control...---- service type: %s, plan: %s', self.service_type_id, self.plan_id)
        r = requests.post(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type_id}/plans/{self.plan_id}/live/toggle_control',
                      auth=(APP_ID, SECRET))

        if json.loads(r.text)['data']['links']['controller'] == None:
            logger.info('You have RELEASED control')
        else:
            logger.info('You have TAKEN control')

    # get id of currently live item in pco live from service_type and plan.
    # Returns logger error and none if plan is not live.
    def get_current_live_item(self):
        logger.debug('attempting to get current live item id')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type_id}/plans/{self.plan_id}/live/current_item_time',
                      auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        try:
            i = data['data']['relationships']['item']['data']['id']
            logger.debug('successfully got current live item id: %s', data['data']['relationships']['item']['data']['id'])
            return data['data']['relationships']['item']['data']['id']
        except TypeError:
            logger.error('Failed to get current live item id for service type %s, plan %s. Is the plan live?', self.service_type_id, self.plan_id)
            return None
        except KeyError:
            logger.error('Failed to get current live item id for service type %s, plan %s. Is the plan live?', self.service_type_id, self.plan_id)
            return None

    # TODO check during a live service. length and length_offset are both 0 when called when out of service time
    def get_current_live_item_time(self):
        logger.debug('getting live item time of service_type %s, plan %s', self.service_type_id, self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                         f'{self.service_type_id}/plans/{self.plan_id}/live/current_item_time',
                         auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        return data

    # returns boolean on if a service is being live controlled or not
    def is_controlled(self):
        logger.debug('Getting controller of live PCO service')
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                      f'{self.service_type_id}/plans/{self.plan_id}/live/',
                         auth=(APP_ID, SECRET))
        data = json.loads(r.text)
        controller = data['data']['links']['controller']

        if controller == None:
            logger.info('Current plan is NOT being live controlled')
            return False
        else:
            logger.info('Current plan IS being live controlled.')
            return True

    # looks at if a plan is being controlled, takes control if it's not. Does nothing if its already controlled
    def take_control(self):
        logger.debug('Taking live plan control...')
        if self.is_controlled() == False:
            self.toggle_control()
        else:
            logger.info('take_control(): Already live controller!')

    # opposite of above function
    def release_control(self):
        logger.debug('Releasing plan control...')
        if self.is_controlled() == True:
            self.toggle_control()
        else:
            logger.info('release_control(): Not live controller!')

    # find the next live item in service, used in pco live setting. This function is needed because headers
    # are considered items in the api, but not the live functionality. Basically this returns the next
    # item that is not a header.
    # Returns None if not currently live
    def find_next_live_item(self):
        pco_plan = PcoPlan(service_type=self.service_type_id, plan_id=self.plan_id)
        items=pco_plan.get_service_items()[1]
        current_live_item = self.get_current_live_item()

        live_item_index = None

        #find index of current live item
        for item in items:
            if item['id'] == current_live_item:
                live_item_index = item['sequence']

        if live_item_index is None:
            logger.debug('pco_live.find_next_live_item: No currently live item, returning None')
            return None

        def find_next_item(n):
            logger.debug('pco_live.find_next_live_item find_next_item recursive function: loop with input %s', n)
            if n > len(items):
                logger.debug('pco_live.find_next_live_item find_next_item recursive function: end of plan!')
                pass
            if not items[n]['type'] == 'header' or None:
                logger.debug('pco_live.find_next_live_item find_next_item recursive function: returning %s,'
                              'item name: %s', items[n]['id'], items[n]['title'])
                return items[n]
            else:
                return find_next_item(n+1)

        return find_next_item(live_item_index)

    def get_current_plan_live_time_id(self):
        logger.debug('get_current_plan_live_time_id: service_type_id: %s, plan_id: %s', self.service_type_id, self.plan_id)
        r = requests.get(f'https://api.planningcenteronline.com/services/v2/service_types/'
                         f'{self.service_type_id}/plans/{self.plan_id}/live/current_item_time/', auth=(APP_ID, SECRET))
        r = json.loads(r.text)
        try:
            logger.debug('Found plan live time id: %s', r['data']['relationships']['plan_time']['data']['id'])
            return r['data']['relationships']['plan_time']['data']['id']
        except KeyError:
            logger.info('get_current_plan_live_time_id: something went wrong, response: ', r)

    # Finds if there is a service after the one that's active now, then advance through all items until the current item id matches the id of the first one in the plan
    def go_to_next_service(self):
        live_service_info = self.pco_plan.get_plan_times()
        current_live_id = self.get_current_plan_live_time_id()

        first_item_id = self.pco_plan.get_service_items()[1][0]['id']

        # loop through service times, find if there is one with a higher id than the one that's live now. Only advances one service.
        has_advanced = False
        for iteration, service in enumerate(live_service_info, start=1):
            if current_live_id < service['id']:
                if not has_advanced:
                    self.take_control()

                    def next():
                        nonlocal has_advanced
                        has_advanced = True
                        self.go_to_next_item()
                        if not self.get_current_live_item() == first_item_id:
                            return next()
                    next()

                    if self.get_current_live_item() == first_item_id:
                        logger.debug('go_to_next_service: success')
            if iteration == len(live_service_info) and has_advanced is False:
                logger.info('go_to_next_service: No action taken. Is there a service after this one?')



if __name__ == '__main__':
    live = PcoLive(service_type_id=824571, plan_id=52371712)
    # live.go_to_next_service()
