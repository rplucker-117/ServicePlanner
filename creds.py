import json
from logzero import logger
import os


class Creds:
    def __init__(self):
        self.creds_file = os.path.join(os.path.dirname(__file__), 'creds.json')

    def create(self):
        print('Please create a PCO Personal Access Token from https://api.planningcenteronline.com/oauth/applications.'
              'This is strictly stored locally on your computer.')
        id = input('Application ID:')
        secret = input('Secret:')

        creds = {
            'APP_ID': id,
            'SECRET': secret
        }

        with open(self.creds_file, 'w') as f:
            f.writelines(json.dumps(creds))
            f.close()
        logger.debug('Created creds.json')

    def read(self):
        try:
            logger.debug('attempting to read creds.json')
            with open(self.creds_file, 'r') as f:
                creds = json.loads(f.read())
                logger.debug('Read creds.json')
                f.close()
                return creds

        except FileNotFoundError as e:
            logger.error('Creds.read: File not found. Exception %s', e)
            self.create()
            self.read()


creds = Creds()

if not os.path.exists(creds.creds_file):
    logger.debug('creds.json doesnt exist. Creating...')
    Creds().create()
else:
    logger.debug('creds.json exists! proceeding')