import os
import json
import subprocess
import sys
import time

from joblib import Parallel, delayed


def write_token(token_path, content):
    with open(token_path, 'w') as token_file:
        token_file.write(content)


def write_error(work_item, exception):
    print('write_error')
    with open('comp.err.log', 'a') as err:
        err.write(str(work_item))
        err.write(' --> ')
        err.write(str(exception))
        err.write('\n')


def work(work_item):
    token_path = work_item['token'] + '.comp'

    if os.path.exists(token_path):
        return

    command = work_item['command']

    try:
        subprocess.check_call(command)
        write_token(token_path, 'ok')
    except Exception as e:
        write_error(work_item, e)


def render_token_written(work_item):
    return os.path.exists(work_item['token'])


def composite_token_written(work_item):
    return os.path.exists(work_item['token'] + '.comp')


if __name__ == '__main__':
    with open('./lists/work_list_comp.json', 'r') as f:
        work_items = json.load(f)

    try:
        os.remove('comp.err.log')
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
