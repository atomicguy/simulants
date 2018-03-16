import os
import json
import subprocess
import sys
import time

error_log = 'rgb.comp.err.log'

from joblib import Parallel, delayed


def write_token(token_path, content):
    with open(token_path, 'w') as token_file:
        token_file.write(content)


def write_error(work_item, exception):
    print('write_error')
    with open(error_log, 'a') as err:
        err.write(str(work_item))
        err.write(' --> ')
        err.write(str(exception))
        err.write('\n')


def token_path(work_item):
    return work_item['token'] + '.comp.rgb'

def work(work_item):

    if composite_token_written(work_item):
        return

    command = work_item['command']

    try:
        subprocess.check_call(command)
        write_token(token_path(work_item), 'ok')
    except Exception as e:
        write_error(work_item, e)


def render_token_written(work_item):
    return os.path.exists(work_item['token'])


def composite_token_written(work_item):
    return os.path.exists(token_path(work_item))


if __name__ == '__main__':
    with open('./lists/work_list_comp_rgb.json', 'r') as f:
        work_items = json.load(f)

    try:
        os.remove(error_log)
    except:
        pass

    def is_done():
        composited_items = [i for i in work_items if composite_token_written(i)]
        num_done = len(composited_items)
        num_total = len(work_items)
        print('composited %d / %d' % (num_done, num_total))
        return num_done == num_total

    while not is_done():
        rendered_items = (i for i in work_items if render_token_written(i) and not composite_token_written(i))
        Parallel(n_jobs=10)(delayed(work)(i) for i in rendered_items)

        time.sleep(60)
