import requests
import json
import pprint
from logzero import logger
import urllib3.exceptions
from typing import Union, List, Dict

class PVP:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.API_BASE_URL = f'http://{self.ip}:{self.port}/api/0'

    def _make_get_request(self, endpoint: str) -> Union[Dict, int]:
        """
        Make a GET request to a specified endpoint
        :param endpoint: The endpoint to make a request to, exactly as it's listed in the documentation including the leading /.
        :return: Deserialized result.
        """

        request_url = f'{self.API_BASE_URL}{endpoint}'

        logger.debug(f'{__class__.__name__}.{self._make_get_request.__name__}: Making get request to endpoint {request_url}.')

        try:
            r = requests.get(request_url)

            if r.status_code == 400:
                return r.status_code

            return r.json()

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):
            logger.warning(f'{__class__.__name__}.{self._make_get_request.__name__}: PVP machine at {self.ip}:{self.port} is either offline, PVP is not running, or the Network API is not configured correctly.')

    def _make_post_request(self, endpoint: str) -> None:
        """
        Make a POST request to a specified endpoint
        :param endpoint: The endpoint to make a request to, exactly as it's listed in the documentation including the leading /.
        :return: None
        """

        request_url = f'{self.API_BASE_URL}{endpoint}'

        logger.debug(f'{__class__.__name__}.{self._make_post_request.__name__}: Making post request to endpoint {request_url}.')

        try:
            requests.post(request_url)

        except (urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError,
                urllib3.exceptions.NewConnectionError,
                ConnectionRefusedError):
            logger.warning(f'{__class__.__name__}.{self._make_post_request.__name__}: PVP machine at {self.ip}:{self.port} is either offline, PVP is not running, or the Network API is not configured correctly.')


    def get_pvp_playlists(self) -> dict:
        """
        Get all playlists.
        :return: All playlists.
        """
        logger.debug(f'{__class__.__name__}.{self.get_pvp_playlists.__name__}: Getting playlists for {self.ip}:{self.port}')
        return self._make_get_request('/data/playlists')

    def get_pvp_layers(self) -> dict:
        """
        Get all layers
        :return: All layers.
        """

        logger.debug(f'{__class__.__name__}.{self.get_pvp_layers.__name__}: Getting layers for {self.ip}:{self.port}')
        return self._make_get_request('/data/layers')

    def is_up(self, timeout: float = 1) -> bool:
        """
        Test to see if a PVP instance is running on the target machine.
        :param timeout: Amount of time to wait before timing out.
        :return: Bool of result.
        """
        logger.debug(f'{__class__.__name__}.{self.is_up.__name__}: Checking to see if PVP instance is up at {self.ip}:{self.port}')

        try:
            requests.get(f'http://{self.ip}:{self.port}/api/0/data/playlists', timeout=timeout)
            return True
        except requests.exceptions.ConnectTimeout:
            logger.warning(f'PVP Machine at IP {self.ip} appears to be DOWN')

        return False

    def does_cue_exist(self, playlist_uuid: str, cue_uuid: str) -> bool:
        """
        Determine if a cue exists on the target PVP machine.
        :param playlist_uuid: playlist uuid that contains the target cue
        :param cue_uuid: uuid of the target cue
        :return: bool of result
        """

        logger.debug(f'{__class__.__name__}.{self.does_cue_exist.__name__}: Checking to see if cue exists on machine {self.ip}:{self.port}. playlist_uuid: {playlist_uuid}, cue_uuid: {cue_uuid}')
        data = self._make_get_request(endpoint=f'/data/playlist/{playlist_uuid}/cue/{cue_uuid}')

        if data == 400:  # method returned status code 400 because cue does not exist
            return False
        if type(data) is dict:  # method returned type dict because cue exists
            return True


    def cue_clip(self, playlist: str, cue: str) -> None:
        """
        Cue a clip inside a playlist. Number only parameters are always interpreted by index and never name.
        :param playlist: can be a uuid, name, or index (integer) of the playlist. The 'Video Input' playlist can be accessed by the -1 index or by UUID.
        :param cue: can be a uuid, name, or index (integer) of the cue or videoInputAction.
        :return: None.
        """

        logger.debug(f'{__class__.__name__}.{self.cue_clip.__name__}: Triggering cue {cue} in playlist {playlist} on machine {self.ip}:{self.port}')

        self._make_post_request(f'/trigger/playlist/{playlist}/cue/{cue}')

    def clear_workspace(self) -> None:
        """
        Clears entire workspace.
        :return: None.
        """
        logger.debug(f'{__class__.__name__}.{self.clear_workspace.__name__}: Clearing workspace on machine {self.ip}:{self.port}')

        self._make_post_request('/clear/workspace')

    def clear_layer(self, layer_id: str) -> None:
        """
        Clear a specific layer.
        :param layer_id: id can be uuid, name, or index. Number only parameters are interpreted as index and never name.
        :return: None.
        """

        logger.debug(f'{__class__.__name__}.{self.clear_layer.__name__}: Clearing layer {layer_id} on machine {self.ip}:{self.port}')

        self._make_post_request(f'/clear/layer/{layer_id}')

    def mute_workspace(self) -> None:
        """
        Mute the entire worskpace.
        :return: None.
        """

        logger.debug(f'{__class__.__name__}.{self.mute_workspace.__name__}: Muting workspace on pvp machine {self.ip}:{self.port}')

        self._make_post_request(f'/mute/workspace')

    def unmute_workspace(self) -> None:
        """
        Unmute the entire workspace
        :return: None.
        """

        logger.debug(f'{__class__.__name__}.{self.unmute_workspace.__name__}: Unmuting workspace on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/unmute/workspace')

    def mute_layer(self, layer_id) -> None:
        """
        Mute a specific layer
        :param layer_id: Can be uuid, name, or index (integer) of the layer that we want to mute
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.mute_layer.__name__}: Muting layer {layer_id} on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/mute/layer/{layer_id}')

    def unmute_layer(self, layer_id) -> None:
        """
        Unmute a specific layer
        :param layer_id: Can be uuid, name, or index (integer) of the layer that we want to mute
        :return:
        """

        logger.debug(f'{__class__.__name__}.{self.mute_layer.__name__}: Unmuting layer {layer_id} on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/unmute/layer/{layer_id}')

    def hide_workspace(self) -> None:
        """
        Hide the entire workspace
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.hide_workspace.__name__}: Hiding workspace on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/hide/workspace')

    def unhide_workspace(self) -> None:
        """
        Unhide the entire workspace
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.unhide_workspace.__name__}: Unhiding workspace on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/unhide/workspace')

    def hide_layer(self, layer_id) -> None:
        """
        Hide a specific layer
        :param layer_id: Can be uuid, name, or index (integer) of the layer that we want to hide. Number only parameters are always interpreted as an index and never name.
        :return: None
        """
        logger.debug(f'{__class__.__name__}.{self.hide_layer.__name__}: Hiding layer {layer_id} on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/hide/layer/{layer_id}')

    def unhide_layer(self, layer_id) -> None:
        """
        Unhide a specific layer
        :param layer_id: Can be uuid, name, or index (integer) of the layer that we want to unhide. Number only parameters are always interpreted as an index and never name.
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.hide_layer.__name__}: Unhiding layer {layer_id} on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/unhide/layer/{layer_id}')

    def pause_workspace(self) -> None:
        """
        Pause the entire workspace
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.pause_workspace.__name__}: Pausing workspace on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/pause/workspace')

    def unpause_workspace(self) -> None:
        """
        Unpause the entire workspace
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.unpause_workspace.__name__}: Unpausing workspace on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/play/workspace')

    def pause_layer(self, layer_id) -> None:
        """
        Pause a specific layer
        :param layer_id: Can be uuid, name, or index (integer) of the layer that we want to unhide. Number only parameters are always interpreted as an index and never name.
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.pause_layer.__name__}: Pausing layer {layer_id} on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/pause/layer/{layer_id}')

    def unpause_layer(self, layer_id) -> None:
        """
        Unpause a specific layer
        :param layer_id: Can be uuid, name, or index (integer) of the layer that we want to unhide. Number only parameters are always interpreted as an index and never name.
        :return: None
        """

        logger.debug(f'{__class__.__name__}.{self.unpause_layer.__name__}: Unpausing layer {layer_id} on pvp machine {self.ip}:{self.port}')
        self._make_post_request(f'/play/layer/{layer_id}')

    def cue_name_from_uuids(self, playlist_uuid: str, cue_uuid: str) -> str | None:
        """
        Get the human readable name of a cue given the playlist and cue uuid
        :param playlist_uuid: can be a uuid, name, or index (integer) of the playlist. The 'Video Input' playlist can be accessed by the -1 index or by UUID.
        :param cue_uuid: can be a uuid, name, or index (integer) of the cue or videoInputAction.
        :return: string of the name of the cue
        """

        logger.debug(f'{__class__.__name__}.{self.cue_name_from_uuids.__name__}: Getting clip name from playlist id {playlist_uuid}, cue uuid {cue_uuid} on machine {self.ip}:{self.port}')
        playlists = self.get_pvp_playlists()

        for playlist in playlists['playlist']['children']:
            if playlist['uuid'] == playlist_uuid:
                for item in playlist['items']:
                    if item['uuid'] == cue_uuid:
                        return item['name']

        return None

    def get_layer_name_from_uuid(self, layer_uuid: str) -> str | None:
        """
        Get the human readable name of a layer given the layer uuid. If layer does not exist, None is returned.
        :param layer_uuid: uuid of layer
        :return: string of the name
        """
        logger.debug(f'{__class__.__name__}.{self.get_layer_name_from_uuid.__name__}: Getting layer name from uuid {layer_uuid} on machine {self.ip}:{self.port}')

        layer = self._make_get_request(f'/data/layer/{layer_uuid}')

        if layer == 400:
            return None

        return layer['layer']['name']


if __name__ == '__main__':
    pvp = PVP(ip='10.1.60.91', port=49343)
    # print(pvp.cue_name_from_uuids(playlist_uuid='FDE14BF5-22BB-4499-8EFB-373C0743B15E', cue_uuid='3A173EFA-50FD-4705-9ABB-E9CDC9F96CC5'))
    pvp.get_layer_name_from_uuid(0)
#Transition video: playlist: FDE14BF5-22BB-4499-8EFB-373C0743B15E, cue: 3A173EFA-50FD-4705-9ABB-E9CDC9F96CC5

