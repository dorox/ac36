import requests
import json
import os
import re

# This race-ids.json" file is not up to date

# r = requests.get("https://www.americascup.com/en/feed/race-ids.json")
# with open("races.json", 'wb') as f:
#     f.write(r.content)
#     races = json.loads(r.content)

# for id, link in races.items():
#     r = requests.get(link)
#     race = json.loads(r.content)
#     n = race["Race"]['RaceNumber']
#     path = 'ACWS/'+ n
#     if n not in os.listdir('ACWS/'):
#         os.mkdir(path)
#     with open(path+'/stats.json', 'wb') as f:
#         f.write(r.content)

def readline(l):
    # Downloads stats.json and binary race data
    if 'DataFile' not in l:
        return
    n =  re.findall(r'\d+', l)[0]
    path = 'ACWS/'+ n

    if n not in os.listdir('ACWS/'):
        os.mkdir(path)

    file = l.split('=')[1].strip()

    if file not in os.listdir(path):
        r2 = requests.get('https://dx6j99ytnx80e.cloudfront.net/racedata/acws2020/'+file)
        with open(path+'/'+file, 'wb') as f:
            f.write(r2.content)
    
    if 'stats.json' not in os.listdir(path):
        r3 = requests.get(f'https://www.americascup.com/AC_Stats/AC36_ACWS_Auckland/Race_{n}.json')
        with open(path+'/'+'stats.json', 'wb') as f:
            f.write(r3.content)
    
r = requests.get('https://dx6j99ytnx80e.cloudfront.net/racedata/acws2020/RacesList.dat')
for l in r.text.splitlines():
    readline(l)
    

