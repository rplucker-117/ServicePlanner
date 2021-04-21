from settings import *
import requests
import json
import pprint

r = requests.get('https://api.planningcenteronline.com/services/v2/service_types/'
                      f'824571/plans/51618293/live/?&include=current_item_time', auth=(APP_ID, SECRET))
pprint.pprint(json.loads(r.text))