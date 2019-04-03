import os
import glob
import json
import subprocess
import sys

from joblib import Parallel, delayed


def find_filepaths(path, extension):
    return glob.glob('%s/*.%s' % (path, extension))


def find_filenames(path, extension):
    return [os.path.basename(path) for path in find_filepaths(path, extension)]


def write_error(work_item, exception):
    print('write_error')
    with open('err.log', 'a') as err:
        err.write(str(work_item))
        err.write(' --> ')
        err.write(str(exception))
        err.write('\n')


def work(work_item):
    sim_name = os.path.splitext(os.path.basename(work_item))[0]
    token_path = os.path.join('tmp/simulants', '{}.blend'.format(sim_name))

    if os.path.exists(token_path):
        print('skipping {}'.format(token_path))
        return

    # json_path = os.path.join('descriptors', '{}.json'.format(work_item))

    command = ['blender', '-b', '-P', 'blender/make_a_simulant.py', '--', '--info', work_item]

    try:
        subprocess.check_call(command)
    except Exception as e:
        write_error(work_item, e)


if __name__ == '__main__':
    work_list = find_filepaths('tmp/jsons', 'json')

    print('found {} items'.format(len(work_list)))

    # prepare file system
    try:
        os.remove('err.log')
    except:
        pass

    Parallel(n_jobs=2)(delayed(work)(i) for i in work_list)
