import os
from logzero import logger
from typing import Dict, List, Union
import json
import pprint


class PersistentPlanData:
    """
    Class for holding data about plans that is persistent between application launches. Data is stored in /configs/persistent_plan_data.json.
    Upon class creation, the file will be read and placed into local_plan_data var. If the file does not exist, it will be created.
    """
    def __init__(self):
        self._abs_path = os.path.dirname(__file__)
        self.local_plan_data = self._read_file()

    def _build_default_file(self):
        """
        Creates the default empty json file in /configs/persistent_plan_data.json
        :return: None.
        """

        logger.info(
            f'{__class__.__name__}.{self._build_default_file.__name__}: Writing empty persistent_plan_data.json file')

        if not os.path.exists(os.path.join(self._abs_path, 'configs', 'persistent_plan_data.json')):
            with open(os.path.join('configs', 'persistent_plan_data.json'), 'w') as f:
                default_content = [
                                    {'id': -1,
                                     'type': 'service_type',
                                     'plans': [{
                                         'id': -2,
                                         'type': 'plan',
                                         'has_been_loaded': True,
                                         'other_custom_value_here': False
                                     },
                                         {
                                            'id': -3,
                                            'type': 'plan',
                                            'has_been_loaded': True,
                                         }

                                     ]}
                                ]
                f.write(json.dumps(default_content))

                logger.info(f'{__class__.__name__}.{self._build_default_file.__name__}: Wrote default persistent_plan_data.json file')

    def _read_file(self) -> List[Dict[str, Union[int, str, List[Dict[str, Union[int, bool]]]]]]:
        """
        Reads and returns the deserialized contents of /configs/persistent_plan_data.json.
        :return: contents of file.
        """

        if os.path.exists(os.path.join(self._abs_path, 'configs', 'persistent_plan_data.json')):
            with open(os.path.join('configs', 'persistent_plan_data.json'), 'r') as f:
                return json.loads(f.read())

        # if the default file does not exist, create it and re run this method
        self._build_default_file()
        return self._read_file()

    def _write_updates_to_disk(self) -> None:
        """
        Write contents of self.local_plan_data to disk.
        :return: None
        """

        with open(os.path.join('configs', 'persistent_plan_data.json'), 'w') as f:
            f.write(json.dumps(self.local_plan_data))

    def _does_service_type_exist(self, service_type_id: int) -> bool:
        """
        Determine if a service type exists in the database
        :param service_type_id: service type id derived from planning center
        :return: bool of result
        """
        service_type_id = int(service_type_id)

        for service_type_dict in self.local_plan_data:
            if service_type_dict['id'] == service_type_id:
                return True

        return False

    def _does_plan_exist(self, service_type_id: int, plan_id: int) -> bool:
        """
        Determines if a plan exists in the database, not necessarily if it has been loaded or not.
        :param service_type_id: service type id derived from planning center
        :param plan_id: plan id derived from planning center
        :return: bool of result
        """
        service_type_id = int(service_type_id)
        plan_id = int(plan_id)

        if not self._does_service_type_exist(service_type_id):
            return False
        else:
            for service_type_dict in self.local_plan_data:
                if service_type_dict['id'] == service_type_id:
                    for plan in service_type_dict['plans']:
                        if plan['id'] == plan_id:
                            return True

        return False

    def has_plan_been_loaded(self, service_type_id: int, plan_id: int) -> bool:
        """
        Determines if a plan has been loaded by the app. This assumes that the plan exists in the database and that the has_been_loaded key exists.
        :param service_type_id: service type id derived from planning center
        :param plan_id: plan id derived from planning center
        :return: bool of result
        """
        service_type_id = int(service_type_id)
        plan_id = int(plan_id)

        if not self._does_plan_exist(service_type_id, plan_id):
            return False
        else:
            for service_type_dict in self.local_plan_data:
                if service_type_dict['id'] == service_type_id:
                    for plan in service_type_dict['plans']:
                        if plan['id'] == plan_id:
                            if plan['has_been_loaded']:
                                return True
                            else:
                                return False

        logger.info(f'{__class__.__name__}.{self.has_plan_been_loaded.__name__}: Attempted to search for plan that did not exist in database')
        return False


    def _add_service_type_to_database(self, service_type_id: int) -> None:
        """
        When a plan type has been loaded, add it to database to keep track of it later. If plan type already exists, skip.
        :param service_type_id: plan type id of the plan that is being loaded, acquired from planning center
        :return: None
        """

        service_type_id = int(service_type_id)

        if not self._does_service_type_exist(service_type_id):
            logger.debug(f'{__class__.__name__}.{self._add_service_type_to_database.__name__}: Adding service type {service_type_id} to database')

            self.local_plan_data.append(
                {'id': service_type_id,
                 'type': 'service_type',
                 'plans': []}
            )

            self._write_updates_to_disk()

    def add_plan_to_database(self, service_type_id: int, plan_id: int) -> None:

        """
        Add a plan to database
        :param service_type_id: plan type id of the plan that is being loaded, acquired from planning center
        :param plan_id: plan id of the plan that is being loaded, acquired from planning center
        :return: None
        """

        service_type_id = int(service_type_id)
        plan_id = int(plan_id)

        self._add_service_type_to_database(service_type_id)

        #if the plan does not already exist in the database, add it
        if not self._does_plan_exist(service_type_id, plan_id):
            for service_type_dict in self.local_plan_data:
                if service_type_dict['id'] == service_type_id:
                    service_type_dict['plans'].append({
                        'id': plan_id,
                        'type': 'plan'
                    })
            self._write_updates_to_disk()

    def add_plan_that_has_been_loaded(self, service_type_id: int, plan_id: int) -> None:
        """
        When a plan has been loaded, add the has_been_loaded: True key.
        :param plan_id: id of the plan that is being loaded, acquired from planning center
        :param service_type_id: plan type id of the plan that is being loaded, acquired from planning center
        :return: local_plan_data after it has been written to disk
        """

        service_type_id = int(service_type_id)
        plan_id = int(plan_id)

        self.add_plan_to_database(service_type_id, plan_id)

        for service_type_dict in self.local_plan_data:
            if service_type_dict['id'] == service_type_id:
                for plan in service_type_dict['plans']:
                    if plan['id'] == plan_id:
                        plan['has_been_loaded'] = True
                        self._write_updates_to_disk()


if __name__ == '__main__':
    ppd = PersistentPlanData()
    pprint.pprint(ppd.local_plan_data)





