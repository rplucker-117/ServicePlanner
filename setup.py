import subprocess
import sys

packages = ['logzero', 'requests', 'zulu', 'demjson', 'pymidi', 'wget', 'Flask', 'ezodf', 'lxml', 'flask_socketio', 'gevent-websocket', 'beautifulsoup4', 'rtmidi2']


def update_pip():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


for package in packages:
    install(package)
