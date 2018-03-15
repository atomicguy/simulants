import os
import json
import random


def get_list(path):
    with open(path) as f:
        list = f.readlines()

    list = [x.strip() for x in list]

    return list


backgrounds = get_list('./lists/backgrounds_list.txt')

with open('./lists/work_list.json', 'r') as f:
    render_list = json.load(f)

composite_list = []

for render in render_list:
    token = render['token']
    comp_id = os.path.split(token)[1]

    layers_path = os.path.join('/usr', 'local', 'share', 'datasets', 'simulants', 'sequences_hair', comp_id)
    background = os.path.join('/usr', 'local', 'share', 'datasets', 'peoplefree', random.choice(backgrounds))
    output = os.path.join('/usr', 'local', 'share', 'datasets', 'simulants', 'sequences_hair_renders', comp_id)

    composite_item = {'composite_id': comp_id,
                      'token': token,
                      'command': ['python', 'composite_video.py',
                                  '--input', layers_path,
                                  '--background', background,
                                  '--output', output]}

    composite_list.append(composite_item)

with open('./lists/work_list_comp.json', 'w') as outfile:
    json.dump(composite_list, outfile, indent=2)
