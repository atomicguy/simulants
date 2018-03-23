from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import random
import subprocess

from argparse import ArgumentParser


def list_files(path_to_annotations, file_extension):
    """Get list of files in a given directory"""
    file_list = []
    for file in os.listdir(path_to_annotations):
        if file.endswith('.' + file_extension):
            file_list.append(file)
    return file_list


def pick_random_images(base_dir, background_dir):
    """Return paths to randomly chosen fore/background images"""
    foreground_list = list_files(base_dir, 'png')
    background_list = list_files(background_dir, 'jpg')

    base_image = random.choice(foreground_list)

    foreground_image = os.path.join(base_dir, base_image)
    background_image = os.path.join(background_dir, random.choice(background_list))

    return {'front': foreground_image, 'back': background_image}


def progress_bar(progress, bar_length=30):
    """Displays or updates a console progress bar

    :param progress: a float percentage between 0 and 1 (i.e. halt to 100%).
    :param bar_length: characters wide the progress bar should be
    """
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(bar_length*progress))
    text = "\rPercent: [{0}] {1}% {2}".format("="*block + " "*(bar_length-block), round(progress*100, 4), status)
    sys.stdout.write(text)
    sys.stdout.flush()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input_dir', '-i', type=str, help='directory of foreground images')
    parser.add_argument('--background_dir', '-b', type=str, help='directory of background images')
    parser.add_argument('--texture', '-t', type=str, help='texture directory')
    parser.add_argument('--matching', '-m', type=str, help='type of color matching to use', default='SAT')
    parser.add_argument('--noise', '-s', type=str, help='type of noise to add', default='')
    parser.add_argument('--num', '-n', type=int, help='number of composites to generate', default=1)
    parser.add_argument('--out_dir', '-o', type=str, help='output directory')
    args = parser.parse_args()

    comp_dir = os.path.join(args.out_dir, 'images')
    if not os.path.exists(comp_dir):
        os.makedirs(comp_dir)
    mask_dir = os.path.join(args.out_dir, 'masks')
    if not os.path.exists(mask_dir):
        os.makedirs(mask_dir)
    head_dir = os.path.join(args.out_dir, 'heads')
    if not os.path.exists(head_dir):
        os.makedirs(head_dir)
    cloth_dir = os.path.join(args.out_dir, 'cloth')
    if not os.path.exists(cloth_dir):
        os.makedirs(cloth_dir)
    body_dir = os.path.join(args.out_dir, 'body')
    if not os.path.exists(body_dir):
        os.makedirs(body_dir)


    i = 1
    for _ in range(args.num):
        progress_bar(i/args.num)
        images = pick_random_images(os.path.join(args.input_dir, 'image_combined'), args.background_dir)
        base_name = os.path.split(images['front'])[1]

        person = images['front']
        background = images['back']
        skin = os.path.join(args.input_dir, 'body_material_index', base_name)
        head = os.path.join(args.input_dir, 'head_material_index', base_name)
        shirt = os.path.join(args.input_dir, 'shirt_material_index', base_name)
        pants = os.path.join(args.input_dir, 'pants_material_index', base_name)
        hair = os.path.join(args.input_dir, 'hair_material_index', base_name)
        ao = os.path.join(args.input_dir, 'ambient_occlusion', base_name)

        texture_list = list_files(args.texture, 'png')
        pants_text = os.path.join(args.texture, random.choice(texture_list))
        shirt_text = os.path.join(args.texture, random.choice(texture_list))

        cmd = ['python', 'combine_layers.py',
               '--person', person,
               '--skin_path', skin,
               '--head', head,
               '--shirt_path', shirt,
               '--pants_path', pants,
               '--hair_path', hair,
               '--ao_path', ao,
               '--background', background,
               '--composite', comp_dir,
               '--mask', mask_dir,
               '--head_out', args.out_dir,
               '--p_tex', pants_text,
               '--s_tex', shirt_text,
               '--matching_method', args.matching,
               '--noise_type', args.noise]

        subprocess.check_call(cmd)
        i += 1
