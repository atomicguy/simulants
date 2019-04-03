# simulants
Tools to generate simulated humanoids for segmentation training

Using Blender and ManuelBastioniLAB to generate images to use in segmentation training.

For more information, check out the story behind these tools: [Simulants: A Synthetic Data System](https://medium.com/@atomicguy/simulants-a-synthetic-data-system-aa26a3099770)


## To Generate Simulant Blends

- generate simulant descriptors (json files)
- run blender with blender/make_a_simulant.py script

(on macOS, blender may need to be added to your Path)

``PYTHONPATH=./ python3 bin/generate_simset.py --number 1``

``blender -b -P bin/blender/make_a_simulant.py -- --info tmp/jsons/[generated_descriptor].json``