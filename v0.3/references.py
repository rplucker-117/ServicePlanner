import json
import pprint
import requests
from settings import *



#get item note category ids, for use in changing item notes
# r = requests.get('https://api.planningcenteronline.com/services/v2/service_types/824571/item_note_categories', auth=(APP_ID, SECRET))

#get item notes for an item
# r = requests.get('https://api.planningcenteronline.com/services/v2/service_types/824571/plans/50469043/items/681842459/item_notes/', auth=(APP_ID, SECRET))
#
# pprint.pprint(json.loads(r.text))



#sample service type stuff
# service_type=824571,
# plan=50469043,
# item_id=681842459,
# item_note_id=243953594,
# app_cue='new cue')

for x in range(1,5):
    print(x)

'item_title': data['attributes']['title'],
                'item_type': data['attributes']['item_type'],
                'person': None,
                'person_notes_item_id': None,
                'producer_notes': None,
                'producer_notes_item_id': None,
                'app_cues': None,
                'app_cues_item_id': None,
                'app_cues_verbose': None,
                'app_cues_note_category_id': app_cue_note_category_id,
                'item_id': data['id'],
                'item_length': data['attributes']['length'],
            }

if cue_dict[len(cue_dict)]['device'] in ('CG3', 'CG4'):
    text_to_update = f"({cue_dict[len(cue_dict)]['device']}):   Cue {cue_dict[len(cue_dict)]['cue_name']}" \
                     f" (playlist {int(cue_dict[len(cue_dict)]['playlist_index']) + 1}, cue {int(cue_dict[len(cue_dict)]['cue_index']) + 1})"
if cue_dict[len(cue_dict)]['device'] == 'Pause':
    text_to_update = f"Pause:   {cue_dict[len(cue_dict)]['time']} seconds."
if cue_dict[len(cue_dict)]['device'] == 'Rosstalk':
    if cue_dict[len(cue_dict)]['type'] == 'cc':
    text_to_update = f"Rosstalk:    CC {cue_dict[len(cue_dict)]['bank']}:{cue_dict[len(cue_dict)]['cc']}"
    if cue_dict[len(cue_dict)]['type'] == 'KEYCUT':
        text_to_update = f"Rosstalk:    KEYCUT {cue_dict[len(cue_dict)]['bus']}, KEY {cue_dict[len(cue_dict)]['key']}"
    if cue_dict[len(cue_dict)]['type'] == 'KEYAUTO':
        text_to_update = f"Rosstalk:    KEYAUTO {cue_dict[len(cue_dict)]['bus']}, KEY {cue_dict[len(cue_dict)]['key']}"
