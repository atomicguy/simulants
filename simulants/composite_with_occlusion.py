from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import uuid
import random
import numpy as np

from PIL import Image, ImageChops
from argparse import ArgumentParser

from combine_layers import make_clothed_person
from combine_layers import generate_overlay
from combine_layers import matching_method
from combine_layers import generate_mask

from pycocotools.coco import COCO


def mkdirp(path):
    """Checks if a directory exists and if not creates the directory"""
    if not os.path.exists(path):
        os.makedirs(path)


def list_files(path_to_annotations, file_extension):
    """Get list of files in a given directory"""
    file_list = []
    for file in os.listdir(path_to_annotations):
        if file.endswith('.' + file_extension):
            file_path = os.path.join(path_to_annotations, file)
            file_list.append(file_path)
    return file_list


def patterns_path(pattern_dir):
    """Return a random texture path"""
    patterns = list_files(pattern_dir, 'png')
    patterns = sorted(patterns)

    return random.choice(patterns)


def background_path(background_dir):
    """Return random background image"""
    backgrounds = list_files(background_dir, 'jpg')
    backgrounds = sorted(backgrounds)

    return random.choice(backgrounds)


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
    text = "\rPercent: [{0}] {1}% {2}".format("="*block + " "*(bar_length-block), round(progress*100,4), status)
    sys.stdout.write(text)
    sys.stdout.flush()


def simulant_id(simulant_dir):
    """Return random simulant id"""
    simulant_paths = list_files(os.path.join(simulant_dir, 'image_combined'), 'png')
    simulant_paths = sorted(simulant_paths)
    simulant_path = random.choice(simulant_paths)

    return os.path.splitext(os.path.split(simulant_path)[1])[0]


def layer_paths(simulant_path, simulant_id):
    base_name = '{}.png'.format(simulant_id)
    person = os.path.join(simulant_path, 'image_combined', base_name)
    skin = os.path.join(simulant_path, 'body_material_index', base_name)
    head = os.path.join(simulant_path, 'head_material_index', base_name)
    shirt = os.path.join(simulant_path, 'shirt_material_index', base_name)
    pants = os.path.join(simulant_path, 'pants_material_index', base_name)
    hair = os.path.join(simulant_path, 'hair_material_index', base_name)
    ao = os.path.join(simulant_path, 'ambient_occlusion', base_name)

    return {'person': person, 'skin': skin, 'head': head, 'shirt': shirt, 'pants': pants, 'hair': hair, 'ao': ao}


def generate_person_overlay(simulant_id, background_path, simulant_dir, pattern_dir):
    """Return a composited simulant over transparency size of background image"""

    layers = layer_paths(simulant_dir, simulant_id)
    shirt_texture = patterns_path(pattern_dir)
    pants_texture = patterns_path(pattern_dir)

    assert len(layers) == 7, 'layers contains {} elements'.format(len(layers))

    person, clothes, head, body = make_clothed_person(layers['person'], layers['skin'], layers['shirt'], layers['pants'],
                                                layers['hair'], layers['ao'], layers['head'], pants_texture,
                                                shirt_texture)

    foreground, clothes_mask, head_mask, body_mask = generate_overlay(person, clothes, head, body, background_path, '',
                                                           scale_min=0.1, scale_max=1.1)

    return {'foreground': foreground, 'clothes': clothes_mask, 'head': head_mask}


# def generate_number_overlays(number, simulant_dir, background_dir, patterns_dir):
#     """Use random overlay to generate number of needed simulants for image
#
#     :param number: number simulant overlays to generate
#     :param simulant_dir: directory of rendered simulant layers
#     :param background_dir: directory of background images
#     :param patterns_dir: directory of clothing texture patterns
#     :return: dict {background: path_to_background, overlays: [{foreground, clothes_mask, head_mask}]}
#     """
#
#     background = background_path(background_dir)
#     overlays = []
#     for i in range(number):
#         sim_id = simulant_id(simulant_dir)
#         overlay = generate_person_overlay(sim_id, background, simulant_dir, patterns_dir)
#         overlays.append(overlay)
#
#     return {'background': background, 'overlays': overlays}


def ensure_dirs(path, name_list):
    """Make sure list of named directories exist, if not create them"""

    paths = {}
    for name in name_list:
        dir_path = os.path.join(path, name)
        mkdirp(dir_path)
        paths[name] = dir_path

    return paths


def mask_with_others(priors, mask, file_path):
    """Save image mask for current objects with what is on top removed

    :param priors: Mask of all objects in front
    :param mask: Mask of current object
    :param file_path: Path (with name) to save mask
    """
    front_mask = ImageChops.invert(priors)
    new_mask = ImageChops.multiply(front_mask, mask)
    new_mask.save(file_path)


# def write_images(comp_source, out_path, composite_id, matching_type):
#     """Write composite images"""
#
#     paths = ensure_dirs(out_path, ['image', 'masks', 'heads', 'clothes'])
#
#     background_path = comp_source['background']
#     overlays = comp_source['overlays']
#
#     bg = Image.open(background_path).convert('RGBA')
#     plate = Image.new('RGBA', bg.size)
#
#     for count, overlay in enumerate(overlays):
#         mask_id = '{}_{}.png'.format(composite_id, str(count).zfill(2))
#         foreground = overlay['foreground']
#         clothes = generate_mask(overlay['clothes'])
#         head = generate_mask(overlay['head'])
#         body_mask = generate_mask(foreground)
#
#         # Start with blank plate, updated on each run
#         plate_mask = generate_mask(plate)
#
#         mask_with_others(plate_mask, body_mask, os.path.join(paths['masks'], mask_id))
#         mask_with_others(plate_mask, clothes, os.path.join(paths['clothes'], mask_id))
#         mask_with_others(plate_mask, head, os.path.join(paths['heads'], mask_id))
#
#         # Update plate with this mask to be used next loop
#         plate = Image.alpha_composite(foreground, plate)
#
#     plate = matching_method(plate, bg, matching_type)
#
#     comp = Image.alpha_composite(bg, plate)
#     comp.save(os.path.join(paths['image'], '{}.png'.format(composite_id)))


def all_annotations_mask(image_id_list):
    """Build mask of all Things in random coco image from list of ids"""
    image_id = random.choice(image_id_list)
    annotation_ids = coco.getAnnIds(imgIds=image_id)
    annotations = coco.loadAnns(annotation_ids)
    masks = [coco.annToMask(a) for a in annotations]
    mask_all_things = np.sum(masks, axis=0)

    # convert mask to 255, uint8, RGBA image
    mask_all_things = (mask_all_things * 255).astype(np.uint8)
    mask_all_things = Image.fromarray(mask_all_things).convert('RGBA')

    return mask_all_things, image_id


def load_image(image_id, images_path):
    """load COCO image based on image id"""
    image_info = coco.loadImgs(ids=image_id)[0]
    filename = image_info['file_name']
    image_path = os.path.join(images_path, filename)
    img = Image.open(image_path).convert('RGBA')

    return img, image_path


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--simulant_dir', type=str, help='directory containing rendered simulant layers')
    parser.add_argument('--backgrounds', type=str, help='directory containing background images')
    parser.add_argument('--patterns', type=str, help='directory of texture patterns')
    parser.add_argument('--out', type=str, help='directory for output composites')
    parser.add_argument('--matching', type=str, help='foreground / background matching method', default='SAT')
    parser.add_argument('--coco_json', type=str, help='path to coco instance json')
    parser.add_argument('--coco_images', type=str, help='path to all coco images')
    parser.add_argument('--number', type=int, help='number of images to generate')
    args = parser.parse_args()

    # load COCO json information and get people free images
    coco = COCO(args.coco_json)
    image_ids = coco.getImgIds()
    image_ids_with_people = coco.getImgIds(catIds = [1])
    image_ids_peoplefree = list(set(image_ids) - set(image_ids_with_people))

    out_paths = ensure_dirs(args.out, ['image', 'person', 'heads', 'clothes', 'occlusion'])

    for i in range(args.number):
        progress_bar((i+1)/args.number)
        thing_mask, image_id = all_annotations_mask(image_ids_peoplefree)
        base_image, base_path = load_image(image_id, args.coco_images)
        sim_id = simulant_id(args.simulant_dir)

        comp_id = '{}_{}.png'.format(image_id, sim_id)

        bottom_layer = base_image.copy
        top_layer = ImageChops.multiply(thing_mask, base_image)
        middle_layers = generate_person_overlay(sim_id, base_path, args.simulant_dir, args.patterns)

        top_mask = generate_mask(top_layer)

        person = generate_mask(middle_layers['foreground'])
        clothes = generate_mask(middle_layers['clothes'])
        head = generate_mask(middle_layers['head'])

        new_person = ImageChops.multiply(ImageChops.invert(top_mask), person)
        new_clothes = ImageChops.multiply(ImageChops.invert(top_mask), clothes)
        new_head = ImageChops.multiply(ImageChops.invert(top_mask), head)

        top_two_layers = Image.alpha_composite(middle_layers['foreground'], top_layer)
        # full_composite = Image.alpha_composite(top_two_layers, bottom_layer)
        #
        # full_composite.save(os.path.join(out_paths['image'], comp_id))
        # new_person.save(os.path.join(out_paths['person'], comp_id))
        # new_clothes.save(os.path.join(out_paths['clothes'], comp_id))
        # new_head.save(os.path.join(out_paths['head'], comp_id))
        # top_layer.save(os.path.join(out_paths['occlusion'], comp_id))
        top_two_layers.save('/tmp/test.png')