import subprocess
import sys

packages = ['Babel',
            'bscpylgtv',
            'Cython',
            'Flask',
            'Flask-SocketIO',
            'MarkupSafe',
            'Pillow',
            'Werkzeug',
            'beautifulsoup4',
            'bidict',
            'certifi',
            'cffi',
            'charset-normalizer',
            'click',
            'colorama',
            'construct',
            'ezodf',
            'future',
            'gevent',
            'gevent-websocket',
            'greenlet',
            'h11',
            'idna',
            'importlib-metadata',
            'iso8601',
            'itsdangerous',
            'jinja2',
            'logzero',
            'lxml',
            'pip',
            'pycparser',
            'pymidi',
            'python-dateutil',
            'python-engineio',
            'python-socketio',
            'pytimeparse',
            'pytz',
            'requests',
            'rtmidi2',
            'setuptools',
            'simple-websocket',
            'six',
            'soupsieve',
            'typing-extensions',
            'urllib3',
            'wakeonlan'
            'wget',
            'wheel',
            'wsproto',
            'zipp',
            'zope.event',
            'zope.interface',
            'zulu']


def update_pip():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == '__main__':
    update_pip()
    for package in packages:
        install(package)
