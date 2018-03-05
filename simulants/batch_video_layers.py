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
            file_list.append(os.path.join(path_to_annotations,file))
    return file_list


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input', '-i', type=str, help='path to directory of simulant blends', required=True)
    parser.add_argument('--hdri', '-d', type=str, help='path to directory of hrdi source images', required=True)
    parser.add_argument('--output', '-o', type=str, help='path to output dir', required=True)
    parser.add_argument('--percent_size', '-p', type=str, help='precent size of 2048', required=True)
    parser.add_argument('--mocap_path', '-m', type=str, help='path to mocap bvh data files', required=True)
    parser.add_argument('--blend_save', '-s', type=str, help='if set, output of saved posed blend', default='')
    args, _ = parser.parse_known_args()

    blend_list = list_files(args.input, 'blend')
    hdri_list = list_files(args.hdri, 'jpg')
    mocap_list = list_files(args.mocap_path, 'bvh')
    mocap_list = sorted(mocap_list)

    i = 1
    for animation in mocap_list:
        base_blend = random.choice(blend_list)
        hdri = random.choice(hdri_list)
        timestamp = file_id = datetime.datetime.now().strftime('%Y%m%d%H%M')
        model = os.path.splitext(os.path.split(base_blend)[1])[0]
        image = os.path.splitext(os.path.split(hdri)[1])[0]
        animation_id = os.path.splitext(os.path.split(animation)[1])[0]
        render_id = '{}-{}-{}'.format(animation_id, model, image)
        out_path = os.path.join(args.output, render_id)

        print('{} of {}'.format(i, len(mocap_list)))
        print('base: {}, image: {}'.format(base_blend, hdri))

        subprocess.check_call(['blender', '-b', '-P', 'render_layers.py',
                               '--',
                               '--blend_in', base_blend,
                               '--background', hdri,
                               '--img_out', out_path,
                               '--render_id', render_id,
                               '--percent_size', args.percent_size,
                               '--blend_save', args.blend_save,
                               '--animation', animation,
                               '--stride', str(1)])
        i += 1