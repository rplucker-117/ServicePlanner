import json
from logzero import logger
import os


class Creds:
    def __init__(self):
        pass

    def create(self):
        print('Please create a PCO Personal Access Token from https://api.planningcenteronline.com/oauth/applications')
        id = input('Application ID:')
        secret = input('Secret:')

        creds = {
            'APP_ID': id,
            'SECRET': secret
        }

        with open('creds.json', 'w') as f:
            f.writelines(json.dumps(creds))
            f.close()
        logger.debug('Created creds.json')

    def read(self):
        try:
            logger.debug('attempting to read creds.json')
            with open('creds.json', 'r') as f:
                creds = json.loads(f.read())
                logger.debug('Read creds.json')
                f.close()
                return creds

        except FileNotFoundError as e:
            logger.error('Creds.read: File not found. Exception %s', e)
            self.create()
            self.read()


if not os.path.exists('creds.json'):
    logger.debug('creds.json doesnt exist. Creating...')
    Creds().create()
else:
    logger.debug('creds.json exists! proceeding')