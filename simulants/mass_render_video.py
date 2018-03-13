import os
import json
import subprocess
import sys

from joblib import Parallel, delayed


def ensure_token_dir(work_item):
    token_path = work_item['token']
    token_dir = os.path.dirname(token_path)

    if not os.path.exists(token_dir):
        os.makedirs(token_dir)


def write_token(token_path, content):
    with open(token_path, 'w') as token_file:
        token_file.write(content)


def write_error(work_item, exception):
    print('write_error')
    with open('err.log', 'a') as err:
        err.write(str(work_item))
        err.write(' --> ')
        err.write(str(exception))
        err.write('\n')


def work(work_item):
    token_path = work_item['token']

    if os.path.exists(token_path):
        return

    command = work_item['command']

    try:
        subprocess.check_call(command)
        write_token(token_path, 'ok')
    except Exception as e:
        write_error(work_item, e)


if __name__ == '__main__':
    with open('./lists/work_list.json', 'r') as f:
        work_list = json.load(f)

    # prepare file system
    ensure_token_dir(work_list[0])
    try:
        os.remove('err.log')
    except:
        pass

    Parallel(n_jobs=10)(delayed(work)(i) for i in work_list)
