"""Generate a json to be used as a multi process job
   list of poses lives in datasets/simulants/mocap_pose_list.txt
"""

import os
import json
import random
import datetime
import subprocess

from argparse import ArgumentParser


def get_list(path):
    with open(path) as f:
        list = f.readlines()
    list = [x.strip() for x in list]

    return list


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--number', '-n', type=int, help='number of renders to generate', required=True)
    parser.add_argument('--out_dir', '-o', type=str, help='output directory for blends', required=True)
    parser.add_argument('--poses', '-p', type=str, help='list of pose paths', required=True)
    parser.add_argument('--token_dir', '-t', type=str, default='/usr/local/share/datasets/simulants/mocap_clothed/tokens')
    args, _ = parser.parse_known_args()

    poses = get_list(args.poses)

    work_items = []

    for _ in range(args.number):
        pose = random.choice(poses)
        command = ['blender', '-b', '-P', 'make_clothed.py',
                   '--',
                   '--base_file', 'data/base_scene.blend',
                   '--clothing', 'data/clothes',
                   '--hair', 'data/hairs',
                   '--out_dir', args.out_dir,
                   '--pose_path', pose]

        job_id = '{}_{}'.format(datetime.datetime.now().strftime('%Y%m%d%H'), os.path.splitext(os.path.basename(pose))[0])
        token = os.path.join(args.token_dir, job_id)

        work_item = {'token': token, 'command': command}
        work_items.append(work_item)

    with open('./lists/mocap_clothed_blends.json', 'w') as outfile:
        json.dump(work_items, outfile, indent=2)