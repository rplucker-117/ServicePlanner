from settings import *
import requests

r = requests.get('https://api.planningcenteronline.com/groups/v2/', auth=(APP_ID, SECRET))
print(r.text)