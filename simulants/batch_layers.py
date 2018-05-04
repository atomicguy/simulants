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
    parser.add_argument('--number', '-n', type=int, help='number of renders to generate', required=True)
    parser.add_argument('--input', '-i', type=str, help='path to directory of simulant blends', required=True)
    parser.add_argument('--hdri', '-d', type=str, help='path to directory of hrdi source images', required=True)
    parser.add_argument('--output', '-o', type=str, help='path to output dir', required=True)
    parser.add_argument('--percent_size', '-p', type=str, help='precent size of 2048', required=True)
    parser.add_argument('--blend_save', '-s', type=str, help='if set, output of saved posed blend', default='')
    args, _ = parser.parse_known_args()

    blend_list = list_files(args.input, 'blend')
    hdri_list = list_files(args.hdri, 'hdr')

    i = 1
    for _ in range(args.number):
        base_blend = random.choice(blend_list)
        hdri = random.choice(hdri_list)
        timestamp = file_id = datetime.datetime.now().strftime('%Y%m%d%H%M')
        model = os.path.splitext(os.path.split(base_blend)[1])[0]
        image = os.path.splitext(os.path.split(hdri)[1])[0]
        render_id = '{}-{}-{}'.format(timestamp, model, image)

        print('{} of {}'.format(i, args.number))
        print('base: {}, image: {}'.format(base_blend, hdri))

        subprocess.check_call(['blender', '-b', '-P', 'render_layers.py',
                               '--',
                               '--blend_in', base_blend,
                               '--background', hdri,
                               '--img_out', args.output,
                               '--render_id', render_id,
                               '--percent_size', args.percent_size,
                               '--blend_save', args.blend_save,
                               '--wrinkles', 'True'])
        i += 1
