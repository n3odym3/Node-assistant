import json

try :
    with open('config/config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
except:
    config = {}