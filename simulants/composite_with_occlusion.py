from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import random
import OpenEXR
import numpy as np

from PIL import Image, ImageChops
from argparse import ArgumentParser

from combine_layers import make_clothed_person
from combine_layers import generate_overlay
from combine_layers import matching_method
from combine_layers import generate_mask

from dataset_toolbox.src.tools import cli, common

from pycocotools.coco import COCO


def patterns_path(pattern_dir):
    """Return a random texture path"""
    patterns = common.read_in_files(pattern_dir, 'png', return_paths=True)
    patterns = sorted(patterns)

    return random.choice(patterns)


def background_path(background_dir):
    """Return random background image"""
    backgrounds = common.read_in_files(background_dir, 'jpg', return_paths=True)
    backgrounds = sorted(backgrounds)

    return random.choice(backgrounds)


def simulant_id(simulant_dir):
    """Return random simulant id"""
    simulant_paths = common.read_in_files(os.path.join(simulant_dir, 'image_combined'), 'png', return_paths=True)
    simulant_paths = sorted(simulant_paths)
    simulant_path = random.choice(simulant_paths)

    return os.path.splitext(os.path.split(simulant_path)[1])[0]


def layer_paths(simulant_path, simulant_id):
    base_name = '{}.png'.format(simulant_id)
    person = os.path.join(simulant_path, 'image_combined', base_name)
    body = os.path.join(simulant_path, 'body_material_index', base_name)
    head = os.path.join(simulant_path, 'head_material_index', base_name)
    shirt = os.path.join(simulant_path, 'shirt_material_index', base_name)
    pants = os.path.join(simulant_path, 'pants_material_index', base_name)
    hair = os.path.join(simulant_path, 'hair_material_index', base_name)
    etc = os.path.join(simulant_path, 'etc_material_index', base_name)
    ao = os.path.join(simulant_path, 'ambient_occlusion', base_name)
    uv = os.path.join(simulant_path, 'uv', simulant_id + '.exr')
    depth = os.path.join(simulant_path, 'z', simulant_id + '.exr')

    return {'person': person, 'body': body, 'head': head, 'shirt': shirt, 'pants': pants, 'hair': hair, 'ao': ao,
            'uv': uv, 'depth': depth, 'etc': etc}


def generate_person_overlay(simulant_id, background_path, simulant_dir, pattern_dir):
    """Return a composited simulant over transparency size of background image"""

    layers = layer_paths(simulant_dir, simulant_id)
    shirt_texture = patterns_path(pattern_dir)
    pants_texture = patterns_path(pattern_dir)

    assert len(layers) == 10, 'layers contains {} elements'.format(len(layers))

    person, clothes, head, body = make_clothed_person(layers['person'], layers['body'], layers['shirt'], layers['pants'],
                                                layers['hair'], layers['ao'], layers['head'], pants_texture,
                                                shirt_texture, layers['uv'], layers['etc'])

    person, clothes_mask, head_mask, body_mask, depth = generate_overlay(person, clothes, head, body, background_path,
                                                                         '', 'BILINEAR', layers['depth'], scale_min=0.1,
                                                                         scale_max=1.1)

    return {'person': person, 'clothes': clothes_mask, 'head': head_mask, 'body': body_mask, 'depth': depth}


def ensure_dirs(path, name_list):
    """Make sure list of named directories exist, if not create them"""

    paths = {}
    for name in name_list:
        dir_path = os.path.join(path, name)
        common.mkdirp(dir_path)
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


def np_array_to_mask(numpy_array):
    """Convert numpy array of ones and zeros into PIL 255 RGBA image"""
    if np.max(numpy_array) > 1:
        numpy_array = np.minimum(np.ones_like(numpy_array), numpy_array)
    mask_uint8 = (numpy_array * 255).astype(np.uint8)
    ones = np.ones_like(mask_uint8) * 255
    mask_rgba = np.stack([ones, ones, ones, mask_uint8], axis=2)
    mask_rgba = Image.fromarray(mask_rgba).convert('RGBA')

    return mask_rgba


def num_annotations(image_id):
    """Return an image with an annotation"""
    annotation_ids = coco.getAnnIds(imgIds=image_id)

    return len(annotation_ids)


def all_annotations_mask(image_id_list, randomize=False):
    """Build mask of all Things in random coco image from list of ids"""
    image_id = random.choice(image_id_list)
    while num_annotations(image_id) == 0:
        image_id = random.choice(image_id_list)
    annotation_ids = coco.getAnnIds(imgIds=image_id)
    annotations = coco.loadAnns(annotation_ids)
    masks = [coco.annToMask(a) for a in annotations]
    mask_all_things = np.sum(masks, axis=0)
    mask_all_things_rgba = np_array_to_mask(mask_all_things)

    if randomize is True:
        mask = random.choice(masks)
        mask_all_things_rgba = np_array_to_mask(mask)

    return mask_all_things_rgba, image_id


def load_image(image_id, images_path):
    """load COCO image based on image id"""
    image_info = coco.loadImgs(ids=image_id)[0]
    filename = image_info['file_name']
    image_path = os.path.join(images_path, filename)
    img = Image.open(image_path).convert('RGBA')

    return img, image_path


def save_layer_mask(layers, layer_name, mask, comp_id, out_paths):
    """Save specified layer with mask cut out of it"""
    layer_mask = generate_mask(layers[layer_name])
    occluded_mask = ImageChops.multiply(ImageChops.invert(mask), layer_mask)
    occluded_mask.save(os.path.join(out_paths[layer_name], comp_id))


def save_masked_depth(depth, mask, comp_id, out_paths):
    comp_id = os.path.splitext(comp_id)[0]
    depth_array = np.asarray(depth).astype(np.float32)
    mask_array = np.asarray(mask).copy()
    mask_array[mask_array > 0] = 1
    mask_array = np.ones_like(mask_array) - mask_array
    depth_data = depth_array * mask_array.astype(np.float32)
    exr = OpenEXR.OutputFile(os.path.join(out_paths['depth'], comp_id + '.exr'), OpenEXR.Header(depth.size[0],
                                                                                                depth.size[1]))
    exr.writePixels({'R': depth_data, 'G': depth_data, 'B': depth_data})


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--simulant_dir', type=str, help='directory containing rendered simulant layers')
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

    out_paths = ensure_dirs(args.out, ['image', 'person', 'head', 'clothes', 'body', 'occlusion', 'depth'])

    for i in range(args.number):
        cli.progress_bar((i+1)/args.number)
        thing_mask, image_id = all_annotations_mask(image_ids_peoplefree, randomize=True)
        base_image, base_path = load_image(image_id, args.coco_images)
        sim_id = simulant_id(args.simulant_dir)

        comp_id = '{}_{}.png'.format(image_id, sim_id)

        blank = Image.new('RGBA', base_image.size)
        top_layer = Image.composite(base_image, blank, thing_mask)
        top_layer.save(os.path.join(out_paths['occlusion'], comp_id))
        top_mask = generate_mask(top_layer)

        middle_layers = generate_person_overlay(sim_id, base_path, args.simulant_dir, args.patterns)
        person = middle_layers['person']
        person = matching_method(np.asarray(person), base_image, args.matching)

        save_layer_mask(middle_layers, 'person', top_mask, comp_id, out_paths)
        save_layer_mask(middle_layers, 'clothes', top_mask, comp_id, out_paths)
        save_layer_mask(middle_layers, 'head', top_mask, comp_id, out_paths)
        save_layer_mask(middle_layers, 'body', top_mask, comp_id, out_paths)
        save_masked_depth(middle_layers['depth'], top_mask, comp_id, out_paths)

        top_two_layers = Image.alpha_composite(person, top_layer)
        full_composite = Image.alpha_composite(base_image, top_two_layers)
        full_composite.save(os.path.join(out_paths['image'], comp_id))
