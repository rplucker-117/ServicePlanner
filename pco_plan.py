import time
import requests
import json
from pprint import pprint
from logzero import logger
import zulu
from creds import Creds
import tkinter.messagebox
from typing import List, Dict, Union


class PcoPlan:
    def __init__(self, **kwargs): # include service_type and plan_id if possible
        if 'service_type' in kwargs:
            self.service_type = kwargs['service_type']
            logger.debug(f'{__class__.__name__}: service_type is {kwargs["service_type"]}')
        if 'plan_id' in kwargs:
            logger.debug(f'{__class__.__name__}: plan_id is {kwargs["plan_id"]}')
            self.plan_id = kwargs['plan_id']

        self._creds = Creds().read()
        self._APP_ID = self._creds['APP_ID']
        self._SECRET = self._creds['SECRET']

        self.API_BASE_URL = 'https://api.planningcenteronline.com'

        self.app_cue_note_category_id: int = None
        self.service_category_app_cue_note_category_id: int = None

    def make_get_request_to_endpoint(self, endpoint: str, expect_404: bool = False) -> dict:
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

    def make_post_request_to_endpoint(self, endpoint: str, payload: dict) -> dict:
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
                          data=json.dumps(payload),
                          auth=(self._APP_ID, self._SECRET))

        # creds have expired
        if r.status_code == 401:
            logger.error(f'API returned status code 401. Credentials have likely expired.')
            tkinter.messagebox.showerror('API Response error',
                                         message=f'API request returned 401. Your API credentials have expired. Please renew them by deleting configs/creds.json and restarting this application.')
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
        :return: Response of PATCH request
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
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                return None

    # ---- GET DATA-----

    def get_all_item_note_ids(self, item_id: int) -> Dict[str, int]:
        """
        Gets the ids of all notes for the given plan item in the given context
        :param item_id: item id
        :return: dict of ids in {'App Cues': '308507798', 'Person': '308507797', 'Timer': '308507799'} form.
        """

        logger.debug(f'{__class__.__name__}.{self.get_all_item_note_ids.__name__}: item id {item_id}')

        response: List[Dict] = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/')['data']

        ids = {}
        for iteration, data in enumerate(response):
            ids.update({data['attributes']['category_name']: int(data['id'])})

        return ids

    def check_if_item_note_exists(self, item_id: int, category_name: str) -> bool:
        """
        Check if a note exists on an item, given the item id and note category name
        :param item_id: item id
        :param category_name: category name, such as 'App Cues' or 'Person'
        :return: bool of result
        """

        logger.debug(f'{__class__.__name__}.{self.check_if_item_note_exists.__name__}: item id {item_id}, category name {category_name}')

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/')
        ''
        for data in response['data']:
            if data['attributes']['category_name'] == category_name:
                return True

        return False

    def get_plan_app_cue_note_id(self) -> Union[int, None]:
        """
        Get the id of the specific note that's associated with the name "App Cues" in the selected plan
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.get_plan_app_cue_note_id.__name__}')

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/')

        for category in response['data']:
            if category['attributes']['category_name'] == 'App Cues':
                return category['id']

        logger.error(f'{self.get_plan_app_cue_note_id.__name__}: Did not find app cue note id. There is probably no note with category name "App Cues"')

        return None

    def get_plan_app_cues(self) -> Union[str, None]:
        """
        Gets content from first plan note with category name "App Cues" and returns it.
        :return: Content from first plan note with name "App Cues", None if there is no note
        """

        logger.debug(f'{__class__.__name__}.{self.get_plan_app_cues.__name__}')

        if self.check_if_plan_app_cue_exists():
            response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes')

            for note in response['data']:
                if note['attributes']['category_name'] == 'App Cues':
                    return note['attributes']['content']
        else:
            logger.debug(f'{__class__.__name__}.{self.get_plan_app_cues.__name__}: No plan app cue note exists')
            return None

    def get_plan_app_cue_note_category_id(self):
        logger.debug(f'{__class__.__name__}.{self.get_plan_app_cue_note_id.__name__}')

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plan_note_categories')

        for category in response['data']:
            if category['attributes']['name'] == 'App Cues':
                logger.debug('get_plan_app_cue_note_id: found app cue note category, id %s', category['id'])
                return category['id']

        logger.error(f'{self.get_plan_app_cue_note_category_id.__name__}: Could not find plan app cue note category id')

        return None

    def get_plan_times(self) -> List[Dict]:
        """
        Gets all scheduled start times of services for a plan
        :return: a list of dicts of plan times containing zulu, local, and the PCO time id
        """

        logger.debug(f'{__class__.__name__}.{self.get_plan_times.__name__}')

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/plan_times/', expect_404=True)

        times = []
        for service_time in response['data']:
            if not service_time['attributes']['time_type'] == 'rehearsal':
                z = service_time['attributes']['starts_at']
                local = zulu.parse(z).format('%Y-%m-%d  %H:%M', tz='local')
                times.append({
                    'z': z,
                    'local': local,
                    'id': service_time['id']
                })

        if not len(times) > 0:
            logger.info(f'{self.get_plan_times.__name__}: Could not find any times associated with plan {self.plan_id}')

        return times

    def get_current_live_service(self):
        # Return dict of currently live plan info, none if plan is not active
        logger.debug(f'{__class__.__name__}.{self.get_current_live_service.__name__}')

        service_times = self.get_plan_times()

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/live/current_item_time/', expect_404=True)

        for service_time in service_times:
            try:
                if service_time['id'] == response['data']['relationships']['plan_time']['data']['id']:
                    return service_time
            except KeyError as e:
                logger.info(f'{self.get_current_live_service.__name__}: Could not find current live service because of an exception: {e}')
                return None

        # this fires if the service_times list is empty
        if len(service_times) == 0:
            logger.info(f'{self.get_current_live_service.__name__}: Could not find current live service as there are no service times')

    def get_service_category_app_cue_note_category_id(self) -> int:
        logger.debug(f'{__class__.__name__}.{self.get_service_category_app_cue_note_category_id.__name__}')

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/item_note_categories')

        for service_type in response['data']:
            if service_type['attributes']['name'] == 'App Cues':
                logger.debug(f'{self.get_service_category_app_cue_note_category_id.__name__} Found id: {service_type["id"]}')
                return int(service_type['id'])

        logger.error(f'{self.get_service_category_app_cue_note_category_id.__name__}: Could not find id')

    def get_plan_note_content(self, note_id):
        # get content of a plan note (different from item note)
        logger.debug(f'{__class__.__name__}.{self.get_plan_note_content.__name__}: note_id: {note_id}')

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{note_id}')

        try:
            return response['data']['attributes']['content']

        except Exception as e:
            logger.error(f'{self.get_plan_note_content.__name__} Exception thrown: {e}, response content: {response}')
            return None

    def check_if_plan_app_cue_exists(self):
        logger.debug(f'{__class__.__name__}.{self.check_if_plan_app_cue_exists.__name__}')

        response = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes')

        for note in response['data']:
            if note['attributes']['category_name'] == 'App Cues':
                return True

        return False

    def get_service_types(self) -> List[Dict]:
        """
        Get all service types that exist in planning center under the current credential's scope.
        :return: list[{name: 'service type name', id: 12345},]
        """

        logger.debug(f'{__class__.__name__}.{self.get_service_types.__name__}')

        response = self.make_get_request_to_endpoint(endpoint=f'/services/v2/service_types/?&per_page=100')

        service_types = []
        for service_type in response['data']:
            service_types.append({
                'name': service_type['attributes']['name'],
                'id': service_type['id']
            })

        return service_types

    def get_services_from_service_type(self, amount_to_return: int = 20) -> List[Dict]:
        """
        Gets services within a service type id. First makes request to get total number of plans, then sets offset based
        on total_count - offset.
        :param amount_to_return: How many plans it returns starting with the most far in advance one, max of 25. Smaller values are faster.
        :return: list of services in [{title: 'service title', series_title: 'series title', date: 'July 16, 2023', id: 12345678}, ] form.
        """

        logger.debug(f'{__class__.__name__}.{self.get_services_from_service_type.__name__}, offset: {amount_to_return}')

        if amount_to_return > 25:
            logger.info(f'Given offset ({amount_to_return}) greater than allowed max. Using 25')
            amount_to_return = 25

        total_items_in_service_type = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans')['meta']['total_count']

        offset = total_items_in_service_type - amount_to_return

        request = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans'
                                   f'?&filter=&offset={offset}')

        services = []
        for service in request['data']:
            services.append({
                'title': service['attributes']['title'],
                'series_title': service['attributes']['series_title'],
                'date': service['attributes']['dates'],
                'id': service['id']
            })

        return services

    def get_assigned_people(self) -> List[Dict]:
        """
        Get all people assigned to the current plan.
        :return: list of dict in [{name: 'John Smith', position: 'Cam 1', status: 'C'},] format.
        """

        logger.debug(f'{__class__.__name__}.{self.get_assigned_people.__name__}')

        total_in_plan: int = self.make_get_request_to_endpoint(f'/services/v2/service_types/'
                                                           f'{self.service_type}/plans/{self.plan_id}/team_members')['meta']['total_count']

        team: List[Dict] = self.make_get_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/team_members?&per_page={total_in_plan}')['data']

        team_members = []

        for person in team:
            team_members.append({
                'name': person['attributes']['name'],
                'position': person['attributes']['team_position_name'],
                'status': person['attributes']['status']
            })

        return team_members

    def get_plan_items(self) -> List[Dict]:
        """
        Get all items in a service. Class parameters service_id and service_type_id must not be null.
        :return: list of dict of relevant service items (title, type, length, service_position, id, sequence, notes)
        """

        logger.debug(f'{__class__.__name__}.{self.get_plan_items.__name__}')

        request = self.make_get_request_to_endpoint(endpoint=f'/services/v2/service_types/'
                                       f'{self.service_type}/plans/{self.plan_id}/items?&include=item_notes,item_times')

        service_items = []
        for service_item in request['data']:
            service_items.append({
                'title': service_item['attributes']['title'],
                'type': service_item['attributes']['item_type'],
                'length': service_item['attributes']['length'],
                'service_position': service_item['attributes']['service_position'],
                'id': service_item['id'],
                'sequence': service_item['attributes']['sequence'],
                'notes': {}
            })

        # add item notes to service items
        for included in request['included']:
            if included['type'] == 'ItemNote':
                item_id = included['relationships']['item']['data']['id']
                for item in service_items:
                    if item['id'] == item_id:
                        dict_key = included['attributes']['category_name']
                        note_content = included['attributes']['content']

                        item['notes'][dict_key] = note_content

        return service_items

    # ---- SEND DATA ----

    def _create_item_app_cues(self, item_id: int, item_note_category_id: int, app_cue: str) -> dict:
        """
        Create "app cues", or add content to the item under note category named "app cues".
        This ONLY works if there is no content in the 'App Cues' Section already. Use the create_and_update_item_app_cue
        method instead.
        :param item_id: the PCO id (ex 12345678) of the item to add content to
        :param item_note_category_id: note category id (ex 12345678) of the category to add content to
        :param app_cue: JSONified string of app cue content
        :return: response from planning center
        """

        logger.debug(f'{__class__.__name__}.{self._create_item_app_cues.__name__}, item_id: {item_id}, item_note_category_id: {item_note_category_id}')

        payload = {'data': {'attributes': {'content': app_cue, 'item_note_category_id': item_note_category_id}}}

        return self.make_post_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/', payload=payload)

    def _update_item_app_cues(self, item_id: int, item_note_id: int, app_cue: str) -> dict:
        """
        Update the app cue data on a plan item. Only works if there is existing data. Use create_and_update_item_app_cue
        instead.
        :param item_id: item id of the plan item containing the app cue
        :param item_note_id: note id of the note to send content to
        :param app_cue: JSONified string of app cue content
        :return: response from PCO
        """

        logger.debug(f'{__class__.__name__}.{self._update_item_app_cues.__name__}, item_id: {item_id}, item_note_id: {item_note_id}')

        payload = {'data': {'attributes': {'content': app_cue}}}

        return self.make_patch_request_to_endpoint(endpoint=f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/{item_note_id}', payload=payload)

    def create_and_update_item_app_cue(self, item_id: int, app_cue: str) -> None:
        """
        Create or update app cues on an item. This should be called instead of the _create_item_app_cues or
        _update_item_app_cues directly.
        :param item_id: item_id: item id of the plan item containing the app cue
        :param app_cue: JSONified string of app cue content
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.create_and_update_item_app_cue.__name__}, item_id: {item_id}')

        if not self.service_category_app_cue_note_category_id:
            self.service_category_app_cue_note_category_id = self.get_service_category_app_cue_note_category_id()

        if self.check_if_item_note_exists(item_id=item_id, category_name='App Cues'):
            item_note_id = self.get_all_item_note_ids(item_id=item_id)
            self._update_item_app_cues(item_id=item_id, item_note_id=item_note_id['App Cues'], app_cue=app_cue)
        else:
            try:
                self._create_item_app_cues(item_id=item_id,
                                           item_note_category_id=self.service_category_app_cue_note_category_id,
                                           app_cue=app_cue)
            except NameError:
                logger.critical('create_and_update_item_app_cue: error. Likely no app cue note category exists')

    def _create_plan_app_cue(self, app_cue: str) -> dict:
        """
        Creates a new note with specified content. Use create_and_update_plan_app_cues instead.
        :param app_cue: JSONified app cue content
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self._create_plan_app_cue.__name__}')

        if not self.app_cue_note_category_id:
            self.app_cue_note_category_id = self.get_plan_app_cue_note_category_id()

        payload = {
                      "data": {
                        "type": "PlanNote",
                        "attributes": {
                          "content": app_cue,
                          "plan_note_category_id": self.app_cue_note_category_id
                        },
                      }
                    }

        return self.make_post_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/', payload=payload)

    def _remove_plan_app_cues(self) -> Union[dict, None]:
        """
        Removes the first note with category name "App Cues" if it exists
        :return: response from PCO, or None if note does not exist
        """

        logger.debug(f'{__class__.__name__}.{self._remove_plan_app_cues.__name__}')

        plan_app_cue_note_id = self.get_plan_app_cue_note_id()

        if not plan_app_cue_note_id:
            logger.error(f'{__class__.__name__}.{self._remove_plan_app_cues.__name__}: Response returned error. There is no note with this id Cancelling request.')
            return None

        return self.make_delete_request_to_endpoint(f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{plan_app_cue_note_id}', expect_404=True)

    def _update_plan_app_cue(self, app_cue: str) -> dict:
        """
        Update plan app cues with new content. Only works if there is an existing note already. Use create_and_update_plan_app_cues instead.
        :param app_cue: JSONified app cue content
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self._update_plan_app_cue.__name__}')

        app_cue_note_id = self.get_plan_app_cue_note_id()

        payload = {'data': {'attributes': {'content': app_cue}}}

        return self.make_patch_request_to_endpoint(endpoint=f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/notes/{app_cue_note_id}',
                                                   payload=payload)

    def create_and_update_plan_app_cues(self, app_cue: str) -> dict:
        """
        Use this when creating or updating any app cues. This will create a new note if one doesnt exist,or update an exiting one if it does.
        :param app_cue: JSONified app cue content
        :return: API response from PCO
        """

        logger.debug(f'{__class__.__name__}.{self.create_and_update_plan_app_cues.__name__}')

        if self.check_if_plan_app_cue_exists():
            return self._update_plan_app_cue(app_cue)
        else:
            return self._create_plan_app_cue(app_cue)

    def remove_item_app_cue(self, item_id) -> None:
        """
        Remove app cues on an item. Deletes the entire note.
        :param item_id: id of the item to remove the note with the name "App Cues" from.
        :return: None.
        """

        logger.debug(f'{__class__.__name__}.{self.include_all_items_in_live.__name__}: Item id: {item_id}')

        #Find the note id that has the user label "App Cues"
        note_ids = self.get_all_item_note_ids(item_id)

        for note_id_key in note_ids.keys():
            if note_id_key == 'App Cues':
                self.make_delete_request_to_endpoint(
                    endpoint=f'/services/v2/service_types/{self.service_type}/plans/{self.plan_id}/items/{item_id}/item_notes/{note_ids[note_id_key]}')

        logger.info(f'{__class__.__name__}.{self.include_all_items_in_live.__name__}: Could not delete app cues for item {item_id}'
                    f'as the note does not exist.')

    def remove_all_item_app_cues(self):
        """
        Remove app cues from ALL items. Keeps plan cues in place.
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.remove_all_item_app_cues.__name__}')

        plan_items = self.get_plan_items()
        for item in plan_items:
            if 'App Cues' in item['notes']:
                self.remove_item_app_cue(item_id=item['id'])

    def include_all_items_in_live(self) -> None:
        """
        Include all items in the plan in "live". If not everything is included, it will break things as
        PCO will skip non-included items when advancing to the next item.
        This should be run upon program launch and app refresh.
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.include_all_items_in_live.__name__}')

        request = self.make_get_request_to_endpoint(f'/services/v2/service_types/'
                                       f'{self.service_type}/plans/{self.plan_id}/items/?&include=item_times')

        # [{'item_id': 12345, 'time_id': 123456789}, ]
        excluded: List[Dict] = []

        for item_time in request['included']:
            if item_time['attributes']['exclude'] is True:

                item = {
                    'item_id': item_time['relationships']['item']['data']['id'],
                    'time_id': item_time['id']
                }

                excluded.append(item)
        if len(excluded) > 0:
            payload = {
                          "data": {
                            "type": "ItemTime",
                            "attributes": {
                              "exclude": False,
                            },
                          }
                        }

            for item in excluded:
                response = self.make_patch_request_to_endpoint(f'/services/v2/service_types/'
                                           f'{self.service_type}/plans/{self.plan_id}/items/{item["item_id"]}/item_times/{item["time_id"]}', payload=payload)

                if response['data']['attributes']['exclude'] is False:
                    logger.debug(f'{__class__.__name__}.{self.include_all_items_in_live.__name__}: Included item id {response["data"]["relationships"]["item"]["data"]["id"]} in live plan')
                else:
                    # it's a big deal if this fails
                    logger.critical(f'{__class__.__name__}.{self.include_all_items_in_live.__name__}: Could not include item id {response["data"]["relationships"]["item"]["data"]["id"]} in live plan.')

    # ---- OTHER ----

    def validate_plan_item_app_cues(self, app_cues: str) -> Union[str, None]:
        """
        Determines if app item cues are valid or not.
        :param app_cues: JSONified string of app cues that are stored in an item
        :return: If cues are valid, return them in the same state they are fed to this function, if not, return None.
        """

        # First, see if it's serializable. If not, return None.
        try:
            data: Dict[str, List[str, int], bool, List[List[str]]] = json.loads(app_cues)

        except json.decoder.JSONDecodeError:
            logger.warning(f'{__class__.__name__}.{self.validate_plan_item_app_cues.__name__}: Invalid json found.')
            return None

        # is 'action_cues' , 'advance_to_next_on_time', and 'advance_to_next_automatically' in the top level keys list?
        for key in data.keys():
            if key not in ('action_cues', 'advance_to_next_on_time', 'advance_to_next_automatically'):
                logger.warning(f'{__class__.__name__}.{self.validate_plan_item_app_cues.__name__}: Invalid key found: {key}.')
                return None

        # is 'action_cues' a list?
        if not type(data['action_cues']) is list:
            logger.warning(f'{__class__.__name__}.{self.validate_plan_item_app_cues.__name__}: action_cues is not a list of cues')
            return None

        # is every cue in action_cue a dict?
        for action_cue in data['action_cues']:
            if not type(action_cue) is dict:
                logger.warning(f'{__class__.__name__}.{self.validate_plan_item_app_cues.__name__}: action_cues {action_cue} is not a dict!')
                return None

        # is each advance_to_next_on_time cue a List[List[str]]?
        for advance_time in data['advance_to_next_on_time']:
            if not type(advance_time) is list:
                logger.warning(f'{__class__.__name__}.{self.validate_plan_item_app_cues.__name__}: advance to next time is not a list!')
                return None
            for time in advance_time:
                if not type(time) is str:
                    logger.warning(f'{__class__.__name__}.{self.validate_plan_item_app_cues.__name__}: advance to next time parameter is not str!')
                    return None

        # is advance_to_next_automatically a bool?
        if not type(data['advance_to_next_automatically']) is bool:
            logger.warning(f'{__class__.__name__}.{self.validate_plan_item_app_cues.__name__}: advance to next automatically is not a bool!')
            return None

        return app_cues


    def validate_plan_cues(self, app_cues: str, push_corrected_data: bool = True) -> Union[str, None]:
        """
        Determines if plan item app cues are valid or not. Pushes corrected data to PCO. This tries its best & isn't
        an end-all be-all.
        :param app_cues: JSONified string of app cues
        :param push_corrected_data: option of pushing corrected data to PCO or not.
        :return: JSONified string of app cues, either in their original form or corrected. None if uncorrectable.
        """

        logger.debug(f'{__class__.__name__}.{self.validate_plan_cues.__name__}')

        has_been_corrected: bool = False

        # first, see if it's serializable. If not, remove the entire note.
        try:
            data: List[List[str, Dict[str, int]]] = json.loads(app_cues)

        except json.decoder.JSONDecodeError:
            logger.warning(f'{__class__.__name__}.{self.validate_plan_cues.__name__}: Invalid json found. Removing plan note.')
            self._remove_plan_app_cues() if push_corrected_data else None
            return None

        #wrap the whole thing in a try except to try to catch anything else unexpected
        try:
            # then, is the first data structure a list?
            if not type(data) is list:
                logger.warning(f'{__class__.__name__}.{self.validate_plan_cues.__name__}: Invalid data found. First data type is not a list')
                self._remove_plan_app_cues() if push_corrected_data else None
                return None

            for i, plan_cue in enumerate(data):
                # Is it a list of lists?
                if not type(plan_cue) is list:
                    logger.warning(f'{__class__.__name__}.{self.validate_plan_cues.__name__}: Invalid data found. Plan cue at index {i} is invalid. (type not list). Removing all plan cues.')
                    self._remove_plan_app_cues() if push_corrected_data else None
                    return None

                # is the first item in the list a string?
                if not type(plan_cue[0]) is str:
                    logger.warning(f'{__class__.__name__}.{self.validate_plan_cues.__name__}: Invalid data found. Plan cue at index {i} is invalid. (Name invalid). Removing cue.')
                    data.remove(plan_cue)
                    has_been_corrected = True

                # is the 2nd item in the list a dict?
                if not type(plan_cue[1]) is dict:
                    logger.warning(f'{__class__.__name__}.{self.validate_plan_cues.__name__}: Invalid data found. Plan cue at index {i} is invalid. (Cue data invalid). Removing cue.')
                    data.remove(plan_cue)
                    has_been_corrected = True

                # is 'action_cues' , 'advance_to_next_on_time', and 'advance_to_next_automatically' in the keys list?
                for key in plan_cue[1].keys():
                    if key not in ('action_cues', 'advance_to_next_on_time', 'advance_to_next_automatically'):
                        logger.warning(f'{__class__.__name__}.{self.validate_plan_cues.__name__}: Invalid data found. Plan cue at index {i} is invalid. (Cue data invalid). Removing cue.')
                        data.remove(plan_cue)
                        has_been_corrected = True
                        pass

            self.create_and_update_plan_app_cues(json.dumps(data)) if has_been_corrected and push_corrected_data else None

            return json.dumps(data)

        except IndexError:
            logger.warning(f'{__class__.__name__}.{self.validate_plan_cues.__name__}: Improperly formatted data found. Removing plan note.')
            self._remove_plan_app_cues() if push_corrected_data else None
            return None


if __name__ == '__main__':
    plan = PcoPlan(service_type=824571, plan_id=67844080)
    pprint(plan.make_get_request_to_endpoint(endpoint='/services/v2/service_types/?&per_page=100'))