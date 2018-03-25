import os
import random
import datetime
import subprocess

from argparse import ArgumentParser


def list_files(path_to_annotations, file_extension):
    """Get list of files in a given directory"""
    file_list = []
    for file in os.listdir(path_to_annotations):
        if file.endswith('.' + file_extension):
            file_list.append(os.path.join(path_to_annotations, file))
    return file_list


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mocap_dir', '-m', type=str, help='directoy of mocap sequences', required=True)
    parser.add_argument('--out_path', '-o', type=str, help='path to output dir', required=True)
    args, _ = parser.parse_known_args()

    mocap_list = list_files(args.mocap_dir, 'bvh')

    for i, mocap in enumerate(sorted(mocap_list)):
        print('{} of {}'.format(i, len(mocap_list)))

        subprocess.check_call(['blender', '-b', '-P', 'extract_pose.py',
                               '--',
                               '--base_file', 'data/base_scene.blend',
                               '--out_dir', args.out_path,
                               '--mocap_path', mocap])
