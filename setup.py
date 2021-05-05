import subprocess
import sys

packages = ['logzero', 'requests', 'zulu', 'demjson', 'pymidi']


def update_pip():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


update_pip()

for package in packages:
    install(package)
