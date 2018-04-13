import os
import glob
import subprocess

from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mocap_dir', '-m', type=str, help='directoy of mocap sequences', required=True)
    parser.add_argument('--out_path', '-o', type=str, help='path to output dir', required=True)
    args, _ = parser.parse_known_args()

    mocap_list = glob.glob(args.mocap_dir + '*.bvh')

    for i, mocap in enumerate(sorted(mocap_list)):
        print('{} of {}'.format(i, len(mocap_list)))

        subprocess.check_call(['blender', '-b', '-P', 'extract_pose.py',
                               '--',
                               '--base_file', 'data/base_scene.blend',
                               '--out_dir', args.out_path,
                               '--mocap_path', mocap])
