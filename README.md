# simulants
Tools to generate simulated humanoids for segmentation training

Using Blender and ManuelBastioniLAB to generate images to use in segmentation training.

For more information, check out the story behind these tools: [Simulants: A Synthetic Data System](https://medium.com/@atomicguy/simulants-a-synthetic-data-system-aa26a3099770)


## To Generate and Render a Simulant

(blender may need to be added to your Path)

``PYTHONPATH=./ python3 bin/simulant_generator.py --out_dir tmp/simulant_jsons --sim_dir tmp/simulant_blends --textures data/patterns --pose_list data/mocap_pose_list.txt --scene_json tmp/scene_jsons --scene_dir tmp/scene_blends --layer_dir tmp/layers``

(adjust output paths as needed)
