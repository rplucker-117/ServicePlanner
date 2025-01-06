import json
from pprint import pprint
import requests
from typing import Union, List, Dict
import urllib3.exceptions
from logzero import logger


class ProPresenter:
    def __init__(self, ip: str, port: int):
        """
        Contains functionality for interacting with ProPresenter
        :param ip: target ip address of the propresenter machine
        :param port: control port under propresenter>preferences>network>Enable Network
        """

        self.ip = ip
        self.port = port

        self.API_BASE_URL = f'http://{self.ip}:{self.port}'

    def is_online(self) -> bool:
        """
        Determines if target propresenter machine is online or not.
        :return: Result. True means machine is online, False means it's offline EITHER due to a config error or other
        (network error, computer being off, etc)
        """
        try:
            r = requests.get(f'{self.API_BASE_URL}/version', timeout=1)
            if r.status_code == 200:
                return True
            else:
                logger.warning(f'{__class__.__name__}.{self.is_online.__name__}: Propresenter machine at {self.ip}:{self.port} is offline.')
                return False

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):

            logger.warning(f'{__class__.__name__}.{self.is_online.__name__}: Propresenter machine at {self.ip}:{self.port} is offline.')
            return False

    def _make_get_request(self, endpoint) -> Union[None, dict, list, str]:
        """
        Make a get request to propresenter
        :param endpoint: endpoint, exactly as it is listed in the documentation, including the leading /
        :return: Result of request, which can be None, list, dict, or str
        """

        logger.debug(f'{__class__.__name__}.{self._make_get_request.__name__}: Making get request to endpoint {endpoint}.')

        try:
            r = requests.get(f'{self.API_BASE_URL}{endpoint}')
            # If response is not 200 or 204, try to return json of response. If can't serialize json, return text.
            if r.status_code not in (200, 204):
                logger.info(
                    f'{__class__.__name__}.{self._make_get_request.__name__} Request to {endpoint} returned status code {r.status_code}')
                return None
            else:
                try:
                    return r.json()
                except json.JSONDecodeError:
                    return r.text

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):
            logger.warning(f'{__class__.__name__}.{self._make_get_request.__name__}: Propresenter machine at {self.ip}:{self.port} is offline.')
            return None

    def _make_delete_request(self, endpoint: str) -> None:
        """
        Make a delete request to an endpoint
        :param endpoint: endpoint, exactly as it is listed in the documentation, including the leading /
        :return: None
        """

        try:
            r = requests.delete(f'{self.API_BASE_URL}{endpoint}')

            if r.status_code == 404:
                logger.warning(f'{__class__.__name__}.{self._make_delete_request.__name__}: Propresenter machine at {self.ip}:{self.port} does not have network enabled or the requested path was not found.')

            elif r.status_code != 204:
                logger.warning(f'{__class__.__name__}.{self._make_delete_request.__name__}: Delete request to endpoint {endpoint} returned status code {r.status_code}')

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):

            logger.warning(f'{__class__.__name__}.{self._make_delete_request.__name__} Propresenter machine at {self.ip}:{self.port} is offline.')
        finally:
            return None

    def _make_put_request(self, endpoint, payload: str) -> None:
        """
        Make a put request to an endpoint
        :param endpoint: endpoint, exactly as it is listed in the documentation, including the leading /
        :param payload: Desired payload
        :return: None
        """
        try:
            r = requests.put(f'{self.API_BASE_URL}{endpoint}', json=payload)

            if r.status_code == 400:
                logger.warning(f'{__class__.__name__}.{self._make_put_request.__name__}: Invalid request.')

            if r.status_code == 404:
                logger.warning(
                    f'{__class__.__name__}.{self._make_put_request.__name__}: Propresenter machine at {self.ip}:{self.port} does not have network enabled or the requested path was not found.')

            elif r.status_code != 204:
                logger.warning(
                    f'{__class__.__name__}.{self._make_put_request.__name__}: Delete request to endpoint {endpoint} returned status code {r.status_code}')

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):

            logger.warning(
                f'{__class__.__name__}.{self._make_put_request.__name__} Propresenter machine at {self.ip}:{self.port} is offline.')
        finally:
            return None

    def get_macros(self) -> List[Dict[str, Dict[str, Union[float, str, int]]]]:
        """
        Retrieves a list of macros that are currently in Propresenter
        :return: List of current macros including color, name, and guid info
        """
        logger.debug(f'{__class__.__name__}.{self.get_macros.__name__} : {self.ip}:{self.port}')

        return self._make_get_request(f'/v1/macros')

    def does_macro_exist(self, macro_uuid: str) -> bool:
        """
        Determines if a macro exists on the target machine or not.
        :param macro_uuid: uuid of the target macro
        :return: bool of result. True if it exists, false if not.
        """

        logger.debug(f'{__class__.__name__}.{self.does_macro_exist.__name__} : {self.ip}:{self.port} : {macro_uuid}')

        macro_list = self.get_macros()

        for macro in macro_list:
            if macro['id']['uuid'] == macro_uuid:
                return True

        return False

    def get_macro_details_from_uuid(self, macro_uuid: str) -> Dict[str, Dict[str, Union[str, float]]]:
        """
        Gets details (name, uuid, color, etc) from uuid)
        :param macro_uuid: uuid of macro
        :return: details of macro
        """

        logger.debug(f'{__class__.__name__}.{self.get_macro_details_from_uuid.__name__} : {self.ip}:{self.port} : {macro_uuid}')

        return self._make_get_request(endpoint=f'/v1/macro/{macro_uuid}')

    def get_current_active_stage_message(self) -> Union[None, str]:
        """
        Gets the current active stage message. Only returns stage message if it is currently active. If the message is hidden, return None.
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.get_current_active_stage_message.__name__}')

        r = self._make_get_request(endpoint=f'/v1/stage/message')
        return None if r == '' else r

    def hide_current_stage_message(self) -> None:
        """
        Hides currently active stage message. Keeps text in stage message text field in place
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.hide_current_stage_message.__name__}')

        self._make_delete_request('/v1/stage/message')

    def show_stage_message(self, message: str) -> None:
        """
        Sets and shows stage message.
        :param message: User facing message to display
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.show_stage_message.__name__} : {message}')

        self._make_put_request(endpoint='/v1/stage/message', payload=message)


    def cue_macro(self, macro_uuid: str) -> None:
        """
        Triggers a macro in propresenter
        :param macro_uuid: guid of the macro retrieved from get_macros
        :return: None
        """
        logger.debug(f'{__class__.__name__}.{self.get_macros.__name__} : {self.ip}:{self.port} : {macro_uuid}')

        self._make_get_request(endpoint=f'/v1/macro/{macro_uuid}/trigger')

if __name__ == '__main__':
    pp = ProPresenter(ip='10.1.51.21', port=1025)
    # pprint(pp.get_macros())
    # pprint(pp.does_macro_exist('C9930416-4902-4AB8-9B67-65175473F6BA'))
    # pprint(pp.cue_macro('C9930416-4902-4AB8-9B67-65175473F6BA'))
    # pprint(pp.get_macro_details_from_uuid('C9930416-4902-4AB8-9B67-65175473F6BA'))
    # pp.is_online()
    # pp.show_stage_message('this is a stage message')
    pp.hide_current_stage_message()