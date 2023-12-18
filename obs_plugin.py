from flask import Flask
import threading
import obspython as obs

app = Flask(__name__)

@app.route('/start_recording', methods=['POST'])
def start():
    obs.obs_frontend_recording_start()
    return 'Started Recording'

@app.route('/stop_recording', methods=['POST'])
def stop():
    obs.obs_frontend_recording_stop()
    return "Stopped Recording"

@app.route('/online_check', methods=['GET'])
def online_check():
    return str(obs.obs_initialized())

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8707)).start()
