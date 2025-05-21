import requests
import json
from typing import Union, List, Dict
from logzero import logger
import urllib3.exceptions
from pprint import pprint

class Resolume:
    def __init__(self, ip: str, port: int):
        """
        Contains functionality for interacting with ProPresenter
        :param ip: listen address under resolume>preferences>Webserver
        :param port: listen port under resolume>preferences>Webserver>Listen Port
        """

        self.ip = ip
        self.port = port

        self.API_BASE_URL = f'http://{self.ip}:{self.port}/api/v1'

    def is_online(self) -> bool:
        try:
            r = requests.get(f'{self.API_BASE_URL}/product')
            if r.status_code == 200:
                return True
            else:
                logger.warning(f'{__class__.__name__}.{self.is_online.__name__}: Resolume machine at {self.ip}:{self.port} is offline.')

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):

            logger.warning(f'{__class__.__name__}.{self.is_online.__name__}: Resolume machine at {self.ip}:{self.port} is offline.')
            return False

    def _make_get_request(self, endpoint: str) -> Union[None, dict, str]:
        """
        Make a get request to resolume
        :param endpoint: endpoint, exactly as it is listed in the documentation, including the leading /
        :return: Result of request, which can be None, list, dict, or str
        """

        logger.debug(f'{__class__.__name__}.{self._make_get_request.__name__}: Making get request to endpoint {endpoint}.')

        try:
            r = requests.get(f'{self.API_BASE_URL}{endpoint}')

            if r.status_code != 200:
                logger.info(f'{__class__.__name__}.{self._make_get_request.__name__} Request to {endpoint} returned status code {r.status_code}')
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
            logger.warning(f'{__class__.__name__}.{self._make_get_request.__name__}: Resolume machine at {self.ip}:{self.port} is offline.')
            return None

    def _make_post_request(self, endpoint: str) -> None:
        """
        Make a post request to resolume
        :param endpoint: endpoint, exactly as it is listed in the documentation, including the leading /
        :return: None
        """
        logger.debug(f'{__class__.__name__}.{self._make_post_request.__name__}: Making post request to endpoint {endpoint}.')

        try:
            r = requests.post(f'{self.API_BASE_URL}{endpoint}')

            if r.status_code not in (200, 204):
                logger.info(f'{__class__.__name__}.{self._make_post_request.__name__} Request to {endpoint} returned status code {r.status_code}')

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):

            logger.warning(f'{__class__.__name__}.{self._make_post_request.__name__} Resolume machine at {self.ip}:{self.port} is offline.')

    def _get_composition(self) -> dict:
        """
        Get the entire resolume composition
        :return: all available data in composition
        """

        logger.debug(f'{__class__.__name__}.{self._get_composition.__name__}: Getting Composition.')

        return self._make_get_request('/composition')
    def _parse_all_layers_simplified(self, composition: dict) -> List[Dict[str, int | str]]:
        layers = composition['layers']

        to_return = []
        for layer in layers:
            to_return.append({
                'id': layer['id'],
                'name': layer['name']['value']
            })

        return to_return

    def get_all_layers_simplified(self) -> List[Dict[str, int | str]]:
        """
        Gets all layers in composition. Returns a list of dicts that contain ids and names.
        :return: list -> dict{id/name}
        """
        logger.debug(f'{__class__.__name__}.{self.get_all_layers_simplified.__name__}: Getting all layers.')

        return self._parse_all_layers_simplified(self._get_composition())

    def _parse_all_layer_groups_simplified(self, composition) -> list[dict]:
        layergroups = composition['layergroups']

        to_return = []
        for layergroup in layergroups:
            layers = []
            for layer in layergroup['layers']:
                layers.append({
                    'id': layer['id'],
                    'name': layer['name']['value']
                })

            to_return.append({
                'id': layergroup['id'],
                'name': layergroup['name']['value'],
                'containing_layers': layers
            })

        return to_return

    def get_all_layer_groups_simplified(self) -> list[dict]:
        """
        Gets all layer groups & layers within those groups.
        :return: list -> dict{id/name/containing_layers}
        """

        logger.debug(f'{__class__.__name__}.{self.get_all_layer_groups_simplified.__name__}: Getting all layergroups.')

        return self._parse_all_layer_groups_simplified(self._get_composition())

    def _parse_all_clips_simplified(self, composition) -> list[dict]:
        clips = []
        layers: list = composition['layers']

        for layer in layers:
            layer_clips: list = layer['clips']
            for clip in layer_clips:
                # Placeholders that are empty are still considered "clips", so we need to have conditions for each case
                # Placeholders that have not been named have state "empty". Placeholders that are empty but named are "disconnected"
                # Placeholders that contain media but are not playing are "disconnected".

                if clip['connected']['value'] == 'Empty':
                    clips.append({
                        'exists': False,
                        'id': clip['id'],
                        'name': clip['name']['value']
                    })

                elif clip['connected']['value'] == 'Disconnected' and clip['video'] is None:
                    clips.append({
                        'exists': False,
                        'id': clip['id'],
                        'name': clip['name']['value']
                    })

                else:
                    clips.append({
                        'exists': True,
                        'id': clip['id'],
                        'name': clip['name']['value'],
                        'thumbnail_id':  clip['thumbnail']['id'],
                        'thumbnail_path': clip['thumbnail']['path'],
                        'containing_layer_id': layer['id'],
                        'file_path': clip['video']['fileinfo']['path'],
                        'description': clip['video']['description']
                    })

        return clips

    def get_all_clips_simplified(self) -> list[dict]:
        """
        Get all clips in the composition. Returns only needed data.
        :return: All clips
        """

        logger.debug(f'{__class__.__name__}.{self.get_all_clips_simplified.__name__}: Getting all clips.')

        return self._parse_all_clips_simplified(self._get_composition())

    def _parse_all_columns_simplified(self, composition) -> list[dict]:
        columns: list = composition['columns']

        to_return = []

        for column in columns:
            to_return.append({
                'id': column['id'],
                'name': column['name']['value']
            })

        return to_return

    def get_all_columns_simplified(self) -> list[dict]:
        logger.debug(f'{__class__.__name__}.{self.get_all_columns_simplified.__name__}: Getting all columns.')

        return self._parse_all_columns_simplified(self._get_composition())

    def get_all_needed_info_simplified(self) -> dict:
        """
        Retreives all information needed for cue creator in single request
        :return:
        """
        composition = self._get_composition()

        return {
            'layers': self._parse_all_layers_simplified(composition),
            'columns': self._parse_all_columns_simplified(composition),
            'layergroups': self._parse_all_layer_groups_simplified(composition),
            'clips': self._parse_all_clips_simplified(composition)
        }

    def disconnect_composition(self) -> None:
        """
        Disconnect all clips in composition
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.disconnect_composition.__name__}: Disconnecting all.')

        self._make_post_request(f'/composition/disconnect-all')

    def disconnect_layer_by_id(self, id: int) -> None:
        """
        Disconnect all clips in a layer
        :param id: layer id
        :return: None
        """
        logger.debug(f'{__class__.__name__}.{self.disconnect_layer_by_id.__name__}: Disconnecting all clips in layer {id}.')

        self._make_post_request(f'/composition/layers/by-id/{id}/clear')

    def disconnect_layer_group_by_id(self, id: int) -> None:
        """
        Disconnect all layers in a layer group
        :param id: id of layer group
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.disconnect_layer_group_by_id.__name__}: Disconnecting layergroup {id}.')

        layergroups = self.get_all_layer_groups_simplified()
        layers_to_disconnect: list[int] = []

        for layergroup in layergroups:
            if layergroup['id'] == id:
                for layer in layergroup['containing_layers']:
                    layers_to_disconnect.append(layer['id'])

        for layer in layers_to_disconnect:
            self.disconnect_layer_by_id(layer)

    def connect_clip_by_id(self, id: int) -> None:
        """
        Connect a clip by id
        :param id: id of clip
        :return: None
        """
        logger.debug(f'{__class__.__name__}.{self.connect_clip_by_id.__name__}: Connecting clip id {id}.')

        self._make_post_request(f'/composition/clips/by-id/{id}/connect')

    def connect_column_by_id(self, id: int) -> None:
        """
        Connect a column by id
        :param id: id of column
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.connect_column_by_id.__name__}: Connecting column id {id}.')

        self._make_post_request(f'/composition/columns/by-id/{id}/connect')

    def get_clip_by_id(self, id: int) -> dict | None:
        """
        Get clip by id. Also Use this to check if clip exists.
        :param id: id of clip or placeholder
        :return: result, none if it does not exist.
        """

        clips = self.get_all_clips_simplified()
        for clip in clips:
            if clip['id'] == id:
                return clip
        return None

    def get_layer_by_id(self, id: int) -> dict | None:
        """
        Get layer by id. Also Use this to check if layer exists.
        :param id: id of layer
        :return: result, none if it does not exist.
        """

        resolume_layers = self.get_all_layers_simplified()
        for layer in resolume_layers:
            if layer['id'] == id:
                return layer
        return None

    def get_layer_group_by_id(self, id: int) -> dict | None:
        """
        Get layer group by id. Also Use this to check if layer group exists.
        :param id: id of layer group
        :return: result, none if it does not exist.
        """

        resolume_layer_groups = self.get_all_layer_groups_simplified()

        for layer_group in resolume_layer_groups:
            if layer_group['id'] == id:
                return layer_group
        return None

    def get_column_by_id(self, id: int) -> dict | None:
        """
        Get column by id. Also Use this to check if column exists.
        :param id: id of column
        :return: result, none if it does not exist.
        """

        resolume_columns = self.get_all_columns_simplified()

        for column in resolume_columns:
            if column['id'] == id:
                return column
        return None

if __name__ == '__main__':
    resolume = Resolume('10.30.0.21', 8080)
    pprint(resolume.get_all_needed_info_simplified())