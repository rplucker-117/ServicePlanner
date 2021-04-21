from settings import *
import json
import requests
import pprint
from pvp import pvp
from rosstalk import rosstalk
import logging
from kipro import kipro

logging.basicConfig(level=log_level)


class cue_coder():

    def reminder_decoder(*self, cuedict):
        logging.debug('Searching for reminders in cue %s', cuedict)
        for iteration, cue in enumerate(cuedict):
            if cuedict[cue]['device'] == 'Reminder':
                reminder = cuedict[cue]['reminder']
                minutes = cuedict[cue]['minutes']
                seconds = cuedict[cue]['seconds']
                total_time = (minutes*60) + seconds

                return reminder, total_time
        else:
            logging.debug('No reminders found in current cue')
            return None


