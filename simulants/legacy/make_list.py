import os
import json
import random


def get_list(path):
    with open(path) as f:
        list = f.readlines()

    list = [x.strip() for x in list]

    return list


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


backgrounds = get_list('./lists/backgrounds_list.txt')
mocaps = get_list('./lists/mocap_list.txt')
simulants = get_list('./lists/simulant_list.txt')

work_items = []

for mocap in mocaps:
    dataset = os.path.join('/usr', 'local', 'share', 'datasets')

    mocap_file = os.path.join(dataset, 'cmu_mocap', mocap)
    blend_file = os.path.join(dataset, 'simulants', 'more_hair', 'blends', random.choice(simulants))
    background = os.path.join(dataset, 'peoplefree', random.choice(backgrounds))

    # Setup ID
    model = os.path.splitext(os.path.split(blend_file)[1])[0]
    image = os.path.splitext(os.path.split(background)[1])[0]
    animation_id = os.path.splitext(os.path.split(mocap_file)[1])[0]
    render_id = '{}-{}-{}'.format(animation_id, model, image)

    # Additional Settings
    output = os.path.join('/usr/local/share/datasets/simulants/sequences_hair', render_id)
    percent_size = str(50)
    stride = str(5)

    work_item = {'render_id': render_id,
                 'token': os.path.join(dataset, 'simulants', 'sequence_check', render_id),
                 'command': ['blender', '-b', '--python-exit-code', '1', '-P', 'render_layers.py', '--',
                 '--blend_in', blend_file,
                 '--background', background,
                 '--render_id', render_id,
                 '--img_out', output,
                 '--percent_size', percent_size,
                 '--animation', mocap_file,
                 '--stride', stride]}

    work_items.append(work_item)

with open('./lists/work_list.json', 'w') as outfile:
    json.dump(work_items, outfile, indent=2)
