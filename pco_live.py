import requests
import json
from logzero import logger
from pco_plan import PcoPlan
from creds import Creds
from typing import List, Dict, Union
import tkinter.messagebox
import time
from pprint import pprint

class PcoLive:
    def __init__(self, service_type_id, plan_id):
        self._creds = Creds().read()
        self._APP_ID = self._creds['APP_ID']
        self._SECRET = self._creds['SECRET']

        self.API_BASE_URL = 'https://api.planningcenteronline.com'

        self.service_type_id = service_type_id
        self.plan_id = plan_id

        self.pco_plan = PcoPlan(service_type=service_type_id, plan_id=plan_id)


    def make_get_request_to_endpoint(self, endpoint: str, expect_404: bool = False, expect_403: bool = False) -> dict:
        """
        Make a get request to a PCO endpoint.
        :param endpoint: an endpoint as listed in planning center's documentation, starting with /services
        for example /services/v2/songs/1/last_scheduled_item/1/item_notes
        :param expect_404: If the response code can be 404, for example, checking current item time
        but the item isn't live, pass True and the function won't return an error
        :return: the python dict object of the response
        """

        logger.debug(f'{__class__.__name__}.{self.make_get_request_to_endpoint.__name__}: endpoint {endpoint}')

        r = requests.get(f'{self.API_BASE_URL}{endpoint}', auth=(self._APP_ID, self._SECRET))

        # creds have expired
        if r.status_code == 401:
            logger.error(f'API returned status code 401. Credentials have likely expired.')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'API request returned 401. Your API credentials have expired. Please renew them by deleting configs/creds.json and restarting this application.')
            return r.json()

        # Some responses can be 404 and not fail, see above
        elif r.status_code == 404 and expect_404:
            return r.json()

        elif r.status_code == 403 and expect_403:
            return r.json()

        elif r.status_code == 404 and not expect_404:
            logger.error(f'Request returned status code 404: {r.text} {r.text}')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}')
            return r.json()

        # rate limit hit
        elif r.status_code == 429:
            logger.warning(f'API rate limit hit. Waiting 10 seconds and retrying.')
            time.sleep(10)
            return self.make_get_request_to_endpoint(endpoint=endpoint)

        # server error
        elif r.status_code in (500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511):
            logger.error(f'Request returned status code {r.status_code}: {r.text}')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}. '
                                                 f'Planning Center may be experiencing issues. \n\n\n {r.text}')
            return r.json()

        # other non-200 response
        elif r.status_code != 200:
            logger.error(f'Request returned status code {r.status_code}: {r.text}')

            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}. \n\n\n {r.text}')
            return r.json()

        else:
            return r.json()

    def make_post_request_to_endpoint(self, endpoint: str, expect_403: bool = False, expect_404: bool=False) -> dict:
        """
        Make a post request to a PCO endpoint, exactly as it is listed in PCO's documentation, starting with /services
        for example /services/v2/songs/1/last_scheduled_item/1/item_notes
        :param endpoint: Endpoint to make the post request to
        :param payload: POST request payload in python dict form
        :return: Response of POST request
        """

        logger.debug(f'{__class__.__name__}.{self.make_post_request_to_endpoint.__name__}: endpoint {endpoint}')

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        r = requests.post(f'{self.API_BASE_URL}{endpoint}',
                          headers=request_headers,
                          auth=(self._APP_ID, self._SECRET))

        # creds have expired
        if r.status_code == 401:
            logger.error(f'API returned status code 401. Credentials have likely expired.')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'API request returned 401. Your API credentials have expired. Please renew them by deleting configs/creds.json and restarting this application.')
            return r.json()

        elif r.status_code == 403 and expect_403:
            return r.json()

        elif r.status_code == 404 and expect_404:
            return r.json()

        # rate limit hit
        elif r.status_code == 429:
            logger.warning(f'API rate limit hit. Waiting 10 seconds and retrying.')
            time.sleep(10)
            return self.make_post_request_to_endpoint(endpoint=endpoint)

        # server error
        elif r.status_code in (500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511):
            logger.error(f'Request returned status code {r.status_code}: {r.text}')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}. '
                                                 f'Planning Center may be experiencing issues. \n\n\n {r.text}')
            return r.json()

        # other non-200 ish response
        elif r.status_code not in (200, 201, 202, 204):
            logger.error(f'Request returned status code {r.status_code}: {r.text}')

            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}. \n\n\n {r.text}')
            return r.json()

        else:
            return r.json()

    def make_patch_request_to_endpoint(self, endpoint: str, payload: dict, expect_404: bool = False) -> dict:
        """
        Make a PATCH request to a PCO endpoint, exactly as it is listed in PCO's documentation, starting with /services
        for example /services/v2/songs/1/last_scheduled_item/1/item_notes
        :param endpoint: Endpoint to make the PATCH request to
        :param payload: PATCH request payload in python dict form
        :param expect_404: If the response code can be 404, for example, checking current item time
        but the item isn't live, pass True and the function won't return an error
        :return: Response of PATCH request
        """

        logger.debug(f'{__class__.__name__}.{self.make_patch_request_to_endpoint.__name__}: endpoint {endpoint}')

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        r = requests.patch(f'{self.API_BASE_URL}{endpoint}',
                          headers=request_headers,
                          data=json.dumps(payload),
                          auth=(self._APP_ID, self._SECRET))

        # creds have expired
        if r.status_code == 401:
            logger.error(f'API returned status code 401. Credentials have likely expired.')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'API request returned 401. Your API credentials have expired. Please renew them by deleting configs/creds.json and restarting this application.')
            return r.json()

        # Some responses can be 404 and not fail, see above
        elif r.status_code == 404 and expect_404:
            return r.json()

        # rate limit hit
        elif r.status_code == 429:
            logger.warning(f'API rate limit hit. Waiting 10 seconds and retrying.')
            time.sleep(10)
            return self.make_post_request_to_endpoint(endpoint=endpoint, payload=payload)

        # server error
        elif r.status_code in (500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511):
            logger.error(f'Request returned status code {r.status_code}: {r.text}')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}. '
                                                 f'Planning Center may be experiencing issues. \n\n\n {r.text}')
            return r.json()

        # other non 200 ish response
        elif r.status_code not in (200, 201, 202, 204):
            logger.error(f'Request returned status code {r.status_code}: {r.text}')

            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}. \n\n\n {r.text}')
            return r.json()

        else:
            return r.json()

    def make_delete_request_to_endpoint(self, endpoint: str, expect_404: bool = False) -> Union[dict, None]:
        """
        Make a DELETE request to a PCO endpoint, exactly as it is listed in PCO's documentation, starting with /services
        for example /services/v2/songs/1/last_scheduled_item/1/item_notes
        :param endpoint: Endpoint to make the DELETE request to
        :param expect_404: If the response code can be 404, for example, checking current item time
        but the item isn't live, pass True and the function won't return an error
        :return: Response of DELETE request
        """

        logger.debug(f'{__class__.__name__}.{self.make_delete_request_to_endpoint.__name__}: endpoint {endpoint}')

        request_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        r = requests.delete(f'{self.API_BASE_URL}{endpoint}',
                          headers=request_headers,
                          auth=(self._APP_ID, self._SECRET))

        # creds have expired
        if r.status_code == 401:
            logger.error(f'API returned status code 401. Credentials have likely expired.')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'API request returned 401. Your API credentials have expired. Please renew them by deleting configs/creds.json and restarting this application.')
            return r.json()

        # Some responses can be 404 and not fail, see above
        elif r.status_code == 404 and expect_404:
            return r.json()

        # rate limit hit
        elif r.status_code == 429:
            logger.warning(f'API rate limit hit. Waiting 10 seconds and retrying.')
            time.sleep(10)
            return self.make_delete_request_to_endpoint(endpoint=endpoint)

        # server error
        elif r.status_code in (500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511):
            logger.error(f'Request returned status code {r.status_code}: {r.text}')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'Delete request to endpoint {endpoint} failed with response code {r.status_code}. '
                                                 f'Planning Center may be experiencing issues. \n\n\n {r.text}')
            return r.json()

        # other non 200 ish response
        elif r.status_code not in (200, 201, 202, 204):
            logger.error(f'Request returned status code {r.status_code}: {r.text}')

            tkinter.messagebox.showerror('API Response error',
                                         message=f'Request to endpoint {endpoint} failed with response code {r.status_code}. \n\n\n {r.text}')
            return r.json()

        else:
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                return None


    def go_to_next_item(self):
        logger.debug(f'{__class__.__name__}.{self.go_to_next_item.__name__}')

        r = self.make_post_request_to_endpoint(f'/services/v2/service_types/{self.service_type_id}/plans/{self.plan_id}/live/go_to_next_item', expect_403=True)

        try:
            if r['errors'][0]['status'] == '403':
                logger.info(f'{__class__.__name__}.{self.go_to_next_item.__name__}: You have not taken live control. Attempting to take control and retry.')
                self.take_control()
                return self.go_to_next_item()
        except KeyError:
            logger.debug(f'{__class__.__name__}.{self.go_to_next_item.__name__}: success')

    def go_to_previous_item(self):
        logger.debug(f'{__class__.__name__}.{self.go_to_previous_item.__name__}')

        r = self.make_post_request_to_endpoint(f'/services/v2/service_types/{self.service_type_id}/plans/{self.plan_id}/live/go_to_previous_item', expect_403=True)

        try:
            if r['errors'][0]['status'] == '403':
                logger.info(f'{__class__.__name__}.{self.go_to_previous_item.__name__}: You have not taken live control. Attempting to take control and retry.')
                self.take_control()
                return self.go_to_previous_item()
        except KeyError:
            logger.debug(f'{__class__.__name__}.{self.go_to_previous_item.__name__}: success')

    # simply toggles control. Use in conjunction with is_controlled for more use
    def toggle_control(self):
        logger.debug(f'{__class__.__name__}.{self.toggle_control.__name__}')

        r = self.make_post_request_to_endpoint(endpoint=f'/services/v2/service_types/{self.service_type_id}/plans/{self.plan_id}/live/toggle_control', expect_404=True)

        try:
            if r['errors'][0]['status'] == '404':
                logger.debug(f'{__class__.__name__}.{self.toggle_control.__name__}: Released control')
        except KeyError:
            controller = r['data']['links']['controller']
            logger.info(f'{__class__.__name__}.{self.toggle_control.__name__}: Took Control')


    # get id of currently live item in pco live from service_type and plan.
    # Returns logger error and none if plan is not live.
    def get_current_live_item(self):
        logger.debug(f'{__class__.__name__}.{self.get_current_live_item.__name__}')

        r = self.make_get_request_to_endpoint(endpoint=f'/services/v2/service_types/{self.service_type_id}/plans/{self.plan_id}/live/current_item_time', expect_404=True)

        try:
            id = r['data']['relationships']['item']['data']['id']
            logger.debug(f'{__class__.__name__}.{self.get_current_live_item.__name__}: Successfully got live item id {id}')
            return id
        except (TypeError, KeyError):
            logger.info(f'{__class__.__name__}.{self.get_current_live_item.__name__}: Failed to get current live item. Is the plan live?')
            return None

    def is_controlled(self) -> bool:
        """
        Returns true if plan is controlled by CURRENTLY AUTHENTICATED API user
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.is_controlled.__name__}')

        live_controller = self.get_live_controller()
        my_id = self.get_my_id()

        if live_controller is None:
            logger.debug(f'{__class__.__name__}.{self.is_controlled.__name__}: Plan is being not controlled')
            return False

        if live_controller == my_id:
            logger.debug(f'{__class__.__name__}.{self.is_controlled.__name__}: Plan is being controlled by authenticated user')
            return True
        else:
            logger.warning(f'{__class__.__name__}.{self.is_controlled.__name__}: Plan is being controlled, but by a different user')
            return False

    def take_control(self):
        logger.debug(f'{__class__.__name__}.{self.take_control.__name__}')

        if not self.is_controlled():
            self.toggle_control()
        else:
            logger.info(f'{__class__.__name__}.{self.take_control.__name__}: already live controller!')

    # opposite of above function
    def release_control(self):
        logger.debug(f'{__class__.__name__}.{self.release_control.__name__}')

        if self.is_controlled() is True:
            self.toggle_control()
        else:
            logger.info(f'{__class__.__name__}.{self.release_control.__name__}: not live controller')

    # find the next live item in service, used in pco live setting. This function is needed because headers
    # are considered items in the api, but not the live functionality. Basically this returns the next
    # item that is not a header.
    # Returns None if not currently live
    def find_next_live_item(self):
        logger.debug(f'{__class__.__name__}.{self.find_next_live_item.__name__}')
        items = self.pco_plan.get_plan_items()
        current_live_item = self.get_current_live_item()

        live_item_index = None

        #find index of current live item
        for item in items:
            if item['id'] == current_live_item:
                live_item_index = item['sequence']

        if live_item_index is None:
            logger.debug(f'{__class__.__name__}.{self.find_next_live_item.__name__}: No item currently live, returning None')
            return None

        def find_next_item(n):
            if n > len(items):
                logger.debug(f'find_next_live_item.{self.find_next_live_item.__name__}: reached end of plan')
                pass
            if not items[n]['type'] == 'header' or None:
                logger.debug(f'find_next_live_item.{self.find_next_live_item.__name__}: found next live item, {items[n]["id"]}, {items[n]["title"]}')
                return items[n]
            else:
                return find_next_item(n+1)

        return find_next_item(live_item_index)

    def get_current_plan_live_time_id(self):
        '''
        Gets id of the current live service, for example, id of the 10:00 or 11:30 service
        :return:
        '''
        logger.debug(f'{__class__.__name__}.{self.get_current_plan_live_time_id.__name__}')

        r = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type_id}/plans/{self.plan_id}/live/current_item_time/')

        try:
            id = r['data']['relationships']['plan_time']['data']['id']
            logger.debug(f'{__class__.__name__}.{self.get_current_plan_live_time_id.__name__} Found live plan time id: {id}')
            return id
        except KeyError:
            logger.error(f'{__class__.__name__}.{self.get_current_plan_live_time_id.__name__}: something went wrong')

    # Finds if there is a service after the one that's active now, then advance through all items until the current item id matches the id of the first one in the plan
    def go_to_next_service(self):
        logger.debug(f'{__class__.__name__}.{self.go_to_next_service.__name__}')

        live_service_info = self.pco_plan.get_plan_times()
        current_live_id = self.get_current_plan_live_time_id()

        first_item_id = self.pco_plan.get_plan_items()[0]['id']

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
                        logger.debug(f'{__class__.__name__}.{self.go_to_next_service.__name__}: Success')
            if iteration == len(live_service_info) and has_advanced is False:
                logger.info(f'{__class__.__name__}.{self.go_to_next_service.__name__}: No action taken. Is there another service after this one?')

    def get_live_controller(self) -> Union[None|int]:
        logger.debug(f'{__class__.__name__}.{self.get_live_controller.__name__}')

        r = self.make_get_request_to_endpoint(endpoint=f'/services/v2/service_types/{self.service_type_id}/plans/{self.plan_id}/live/controller', expect_404=True)

        controller_id: Union[None | int] = None
        try:
            controller_id = int(r['data']['id'])
            logger.debug(f'{__class__.__name__}.{self.get_live_controller.__name__}: Found live controller with id {controller_id}')
        except KeyError:
            controller_id: None
            logger.info(f'{__class__.__name__}.{self.get_live_controller.__name__}: No controller found. Is the plan being controlled?')

        return controller_id


    def get_my_id(self) -> int:
        """
        Finds id of currently authenticated user.
        This is a bit of a hack as there is no way to find current user strictly through Services API.
        It intentionally gets an item that it does not have permission for and reads the error message, which returns "user x does not have permission...".
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.get_my_id.__name__}')

        r = self.make_get_request_to_endpoint(endpoint=f'/api/v2/', expect_403=True)
        error_message = r['errors'][0]['meta']['description']
        id: int = int(error_message[13:].split(' ')[0])

        logger.debug(f'{__class__.__name__}.{self.get_my_id.__name__} Found current authenticated user id with id {id}')

        return id


if __name__ == '__main__':
    live = PcoLive(service_type_id=824571, plan_id=78022135)

