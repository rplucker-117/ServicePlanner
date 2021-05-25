from flask import Flask, render_template, request, redirect
import requests
import json
from logzero import logger
import pprint
import urllib.parse
from flask_socketio import SocketIO, emit

app = Flask(__name__)
async_mode=None
socketio = SocketIO(app, async_mode=async_mode)


main_app = None

@app.route('/')
def home():
    logger.debug('Serving /')
    return render_template('index.html', sync_mode=socketio.async_mode,
                           plan_data=main_app.main_ui.plan_items, live_index = main_app.main_ui.current_item_index)


@app.route('/action', methods=['POST'])
def update():
    if request.method == 'POST':
        logger.debug('flask_server.update: received post data. json:  %s, form: %s', request.json, request.form)

        if len(request.form.keys()) > 0:
            # request is from web, post data is received as form
            if request.form['action'] == 'web_next':
                logger.debug('flask_server.update: received next command from web')
                main_app.main_ui.next(from_web=True, cue_items=request.form['cue'])
                return app.response_class(response='OK',
                                          status=200,
                                          mimetype='application/json')

            if request.form['action'] == 'web_previous':
                logger.debug('flask_server.update: received next command from web')
                main_app.main_ui.previous(from_web=True, cue_items=request.form['cue'])
                return app.response_class(response='OK',
                                          status=200,
                                          mimetype='application/json')
        else:
            # request is from app, post data is sent as json rather than form data
            data = json.loads(request.json)

            if data['action'] == 'app_next':
                logger.debug('flask_server.update: sending next request to active sites')
                socketio.emit('test message', broadcast=True) #todo make this work

    return 'something'

@socketio.on('my event')
def handle_message(data):
    print(data)

def start(startup_class):
    global main_app
    main_app = startup_class
    socketio.run(host='0.0.0.0', port=80, app=app)
