from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import uuid
import subprocess

from argparse import ArgumentParser

def get_file_list(path, extension):
    file_list = []
    for file in os.listdir(path):
        if file.endswith('.{}'.format(extension)):
            file_list.append(file)

    return file_list


def out_dir(out_path, name):
    new_dir = os.path.join(out_path, name)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)

    return new_dir


def make_background_video(image_path, video_dir, number_frames):
    cmd = ['python', 'image_pan.py',
           '--input', image_path,
           '--output', video_dir,
           '--number_frames', str(number_frames)]
    print(cmd)

    subprocess.check_call(cmd)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input', '-i', type=str, help='input directory containing mocap video layers', required=True)
    parser.add_argument('--background', '-b', type=str, help='path to background image', required=True)
    parser.add_argument('--output', '-o', type=str, help='output directory', required=True)
    args = parser.parse_args()

    input = args.input

    person_path = os.path.join(input, 'image_combined')
    frame_list = get_file_list(person_path, 'png')
    frame_list = sorted(frame_list)
    num_frames = len(frame_list)

    background_video_dir = out_dir(args.output, 'background')
    composite_dir = out_dir(args.output, 'composite')
    mask_dir = out_dir(args.output, 'masks')
    head_dir = out_dir(args.output, 'heads')

    make_background_video(args.background, background_video_dir, num_frames)
    background_frames = sorted(get_file_list(background_video_dir, 'png'))

    assert len(background_frames) == num_frames, 'number of background and foreground frames do not match'

    seed = str(uuid.uuid4())

    for front, back in zip(frame_list, background_frames):
        person = os.path.join(input, 'image_combined', front)
        skin = os.path.join(input, 'skin_material_index', front)
        shirt = os.path.join(input, 'shirt_material_index', front)
        pants = os.path.join(input, 'pants_material_index', front)
        hair = os.path.join(input, 'skin_material_index', front)
        ao = os.path.join(input, 'ambient_occlusion', front)
        head = os.path.join(input, 'head_material_index', front)
        background = os.path.join(background_video_dir, back)
        name = front[:-4]

        cmd = ['python', 'combine_layers.py',
               '--person', person,
               '--skin_path', skin,
               '--shirt_path', shirt,
               '--pants_path', pants,
               '--hair_path', hair,
               '--ao_path', ao,
               '--background', background,
               '--composite', composite_dir,
               '--mask', mask_dir,
               '--type', 'video',
               '--out_name', name,
               '--seed', seed,
               '--head', head,
               '--head_out', head_dir]

        # print(cmd)

        subprocess.check_call(cmd)
