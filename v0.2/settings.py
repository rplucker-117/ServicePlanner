APP_ID = '10b467989a18dea7fea1c705fb0137bd707005803296580c3df7e96d6d718684'
SECRET = 'dfebbffd40ce49ee7a511c400c612808899b35c2a61fc3c8ba1ddbb6fd906ef7'


log_level = 10

# CRITICAL: 50
# ERROR: 40
# WARNING: 30
# INFO: 20
# DEBUG: 10

app_cue_note_category_id = 4141733 #id of note category for "App Cues". Got from
# https://api.planningcenteronline.com/services/v2/service_types/824571/item_note_categories.

bg_color = '#2b2b2b'
header_color = '#8c8c8c'
header_font_size = 11
text_color = '#d1d1d1'
song_title_color = '#5ec9ff'
font = 'Arial'
item_font = 'Arial'
song_font = 'Arial'
plan_text_size = 14
other_text_size = 12
producer_note_text_size = 10
live_color = '#a34444'

accent_color_1 = '#ffc638'
accent_text_color = '#2b2b2b'
accent_text_size = 18
accent_text_font = 'Arial Bold'

clock_text_color = text_color
clock_text_size = 38
clock_text_font = 'Arial Bold'
clock_overrun_color = '#a34444'
clock_section_live_item_text_size = 32

app_cue_font_size = 7

text_entry_box_bg_color = '#444444'

cg3_ip = '10.1.60.95'
cg3_port = '49868'

cg4_ip = '10.1.51.29'
cg4_port = '49188'

current_cues_text_size = 11

options_button_text_size = 10

ui_debug_color = '#7aa825'
item_separator_color = '#dddddd'

reminder_color = '#1c1c1c'
reminder_font_size = 20

resi_ip = 'x.x.x.x'
resi_port = '7788'

rosstalk_ip = '10.1.60.13'
rosstalk_port = 7788

delay_kipro_start = True
#adds .5s of delay between multiple kipros, so they import in the correct order in a nle

kipro_data = {
    0: {
         'name': 'ALL',
         'ip': '*'
    },
    1: {
        'name': 'REC1_CAM8',
        'ip': '10.1.60.14'
    },
    2: {
        'name': 'REC2_CAM1',
        'ip': '10.1.60.15'
    },
    3: {
        'name': 'REC3_CAM2',
        'ip': '10.1.60.20'
    },
    4: {
        'name': 'REC4_CAM3',
        'ip': '10.1.60.87'
    },
    5: {
        'name': 'REC5_CAM4',
        'ip': '10.1.60.88'
    },
    6: {
        'name': 'REC6_CAM5',
        'ip': '10.1.60.89'
    },
    7: {
        'name': 'REC7_CAM6',
        'ip': '10.1.60.86'
    },
    8: {
        'name': 'REC8_CAM7',
        'ip': '10.1.60.124'
    }
}
