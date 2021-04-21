#
log_level = 10

# CRITICAL: 50
# ERROR: 40
# WARNING: 30
# INFO: 20
# DEBUG: 10

app_cue_note_category_id = 4141733

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
producer_note_text_size = 9
live_color = '#a34444'
default_font = 'Arial'
item_time_size = 8
plan_item_frame_width = 1000

separator_color ='#3f3f3f'

accent_color_1 = '#ffc638'
accent_text_color = '#2b2b2b'
accent_text_size = 18
accent_text_font = 'Arial Bold'

clock_text_color = text_color
clock_text_size = 38
clock_text_font = 'Arial Bold'
clock_overrun_color = '#a34444'
clock_section_live_item_text_size = 32

app_cue_font_size = 6

text_entry_box_bg_color = '#444444'

display_kipros = True

kipro_idle_color = '#317c42'
kipro_recording_color = live_color
kipro_error_color = '#ff0000'
kipro_unable_to_commmunicate_color = '#7a7a7a'

interval_update_kipros = True
kipro_update_interval = 30000 # in seconds. Only applies if interval_update_kipros and display_kipros is True.

global_cue_font_size = 11

cg3_ip = '10.1.60.95'
cg3_port = '49868'

cg4_ip = '10.1.51.29'
cg4_port = '49188'

current_cues_text_size = 11

options_button_text_size = 10

ui_debug_color = '#7aa825'
item_separator_color = '#dddddd'

reminder_color = '#1c1c1c'
reminder_font_size = 24

resi_ip = '10.2.60.101'
resi_port = '7788'

rosstalk_ip = '10.1.60.13'
rosstalk_port = 7788

delay_kipro_start = True
#adds .5s of delay between multiple kipros, so they import in the correct order in a nle

kipro_timeout_threshold = 1 #in seconds

# how often to refresh live adjacent plan
adjacent_plan_refresh_interval = 5

kipro_data = {
    0: {
         'name': 'ALL',
         'ip': '*'
    },
    1: {
        'name': 'REC1_CAM1',
        'ip': '10.1.60.14'
    },
    2: {
        'name': 'REC2_CAM2',
        'ip': '10.1.60.15'
    },
    3: {
        'name': 'REC3_CAM3',
        'ip': '10.1.60.20'
    },
    4: {
        'name': 'REC4_CAM4',
        'ip': '10.1.60.87'
    },
    5: {
        'name': 'REC5_CAM5',
        'ip': '10.1.60.88'
    },
    6: {
        'name': 'REC6_CAM6',
        'ip': '10.1.60.89'
    },
    7: {
        'name': 'REC7_CAM7',
        'ip': '10.1.60.86'
    },
    8: {
        'name': 'REC8_CAM8',
        'ip': '10.1.60.85'
    }
}

kipros_new = [
    {
        'name': 'ALL',
         'ip': '*'
    },
    {
        'name': 'REC1_CAM1',
        'ip': '10.1.60.14'
    },
    {
        'name': 'REC2_CAM2',
        'ip': '10.1.60.15'
    },
    {
        'name': 'REC3_CAM3',
        'ip': '10.1.60.20'
    },
    {
        'name': 'REC4_CAM4',
        'ip': '10.1.60.87'
    },
    {
        'name': 'REC5_CAM5',
        'ip': '10.1.60.88'
    },
    {
        'name': 'REC6_CAM6',
        'ip': '10.1.60.89'
    },
    {
        'name': 'REC7_CAM7',
        'ip': '10.1.60.86'
    },
    {
        'name': 'REC8_CAM8',
        'ip': '10.1.60.85'
    }
]