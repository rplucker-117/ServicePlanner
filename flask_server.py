from flask import Flask, request
from flask_socketio import SocketIO
from main import MainUI
from threading import Thread
from logzero import logger
from global_cues import GlobalCues
from pprint import pprint

app = Flask(__name__)

# this is the instance of the main ui. It's set in the start function below.
main_app: MainUI


@app.route('/next', methods=['POST'])
def next():
    main_app.next(cue_items=True)
    return 'Request received successfully.'


@app.route('/previous', methods=['POST'])
def previous():
    main_app.previous(cue_items=True)
    return 'Request received successfully.'


@app.route('/previous_no_actions', methods=['POST'])
def previous_no_actions():
    main_app.previous(cue_items=False)
    return 'Request received successfully.'


@app.route('/next_no_actions', methods=['POST'])
def next_no_actions():
    main_app.next(cue_items=False)
    return 'Request received successfully.'

@app.route('/activate_plan_cue/<int:plan_cue_number>', methods=['POST'])
def plan_cue(plan_cue_number: int):
    plan_cues = main_app.plan_cues
    cue_handler = main_app.cue_handler

    cue_data = plan_cues[plan_cue_number-1][1]
    Thread(target=cue_handler.activate_cues(cue_data['action_cues'])).start()

    return 'Request received successfully.'

# takes post requests at http://localhost:80/activate_global_cue?&bank=2&cue_index=3
@app.route('/activate_global_cue', methods=['POST'])
def activate_global_cue():
    bank: int = int(request.args.get('bank')) - 1
    cue_index: int = int(request.args.get('cue_index')) - 1

    logger.debug(f'{activate_global_cue.__name__}: Activating global cue from POST request. Bank {bank}, cue index {cue_index}')

    cue_handler = main_app.cue_handler
    global_cues = GlobalCues().read_global_cues()
    cue_data = global_cues[bank][cue_index]['cues']
    cue_handler.activate_cues(cue_data)

    return 'Request received successfully'


def start_flask_server(main_ui: MainUI):
    logger.debug('starting webserver')
    global main_app
    main_app = main_ui
    app.run('0.0.0.0', 7777)
