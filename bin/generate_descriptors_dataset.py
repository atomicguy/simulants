from __future__ import absolute_import, division, print_function

import os
import json
import random
import subprocess
import uuid

from argparse import ArgumentParser
from dataset_toolbox.src.tools.cli import progress_bar
from dataset_toolbox.src.tools.common import find_filepaths, get_list
from simulants.description import update_layers


distribution = {0: 4826,
                1: 17293,
                2: 7663,
                3: 4192,
                4: 2757,
                5: 1959,
                6: 1450,
                7: 1193,
                8: 1027,
                9: 858,
                10: 869,
                11: 865,
                12: 815,
                13: 956,
                14: 3268,
                15: 6,
                16: 1,
                18: 1,
                20: 1}


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--sims_dir', type=str, help='directory of sim descriptors', required=True)
    parser.add_argument('--out_dir', type=str, help='output dir for scene json files', required=True)
    parser.add_argument('--backgrounds', type=str, help='directory of backround images', required=True)
    args = parser.parse_args()

    loc_distributions = ['uniform', 'beta']

    for sim_count, number in distribution.iteritems():
        print('scenes containing {} simulants\n'.format(sim_count))
        for i in range(number):
            progress_bar((i+1)/number)

            cmd = ['python', 'generate_scene_description.py',
                   '--out_dir', args.out_dir,
                   '--scene_dir', '/tmp',
                   '--sims', args.sims_dir,
                   '--number', str(sim_count),
                   '--distribution', random.choice(loc_distributions),
                   '--backgrounds', args.backgrounds]

            subprocess.check_call(cmd)
