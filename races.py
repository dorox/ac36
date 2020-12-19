import requests
import json
import os

r = requests.get("https://www.americascup.com/en/feed/race-ids.json")
with open("races.json", 'wb') as f:
    f.write(r.content)
    races = json.loads(r.content)

for id, link in races.items():
    r = requests.get(link)
    race = json.loads(r.content)
    n = race["Race"]['RaceNumber']
    path = 'ACWS/'+ n
    if n not in os.listdir('ACWS/'):
        os.mkdir(path)
    with open(path+'/stats.json', 'wb') as f:
        f.write(r.content)
