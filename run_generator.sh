#!/bin/bash

PYTHONPATH=./ python bin/simulant_generator.py --out_dir tmp/simulant_jsons --sim_dir tmp/simulant_blends --textures data/patterns --pose_list data/mocap_pose_list.txt --scene_json tmp/scene_jsons --scene_dir tmp/scene_blends --layer_dir tmp/layers