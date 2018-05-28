import os
import json
import subprocess
import sys

from joblib import Parallel, delayed


def write_error(work_item, exception):
    print('write_error')
    with open('err.log', 'a') as err:
        err.write(str(work_item))
        err.write(' --> ')
        err.write(str(exception))
        err.write('\n')


def work(work_item):
    token_path = work_item['path']

    if os.path.exists(token_path):
        print('skipping {}'.format(token_path))
        return

    json_path = os.path.join('descriptors', '{}.json'.format(work_item['id']))

    command = ['blender', '-b', '-P', 'make_a_simulant.py', '--', '--info', json_path]

    try:
        subprocess.check_call(command)
    except Exception as e:
        write_error(work_item, e)


if __name__ == '__main__':
    with open('simulant_set.json', 'r') as f:
        work_list = json.load(f)

    print('found {} items'.format(len(work_list)))

    # prepare file system
    try:
        os.remove('err.log')
    except:
        pass

    Parallel(n_jobs=5)(delayed(work)(i) for i in work_list)
