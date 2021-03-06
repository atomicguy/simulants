# simulants

![Simulant Wall](https://res.cloudinary.com/atomic/image/upload/v1560658645/simulant_wall_rbauln.gif)

Tools to generate simulated humanoids for segmentation training

Using Blender and ManuelBastioniLAB to generate images to use in segmentation training.

For more information, check out the story behind these tools: [Simulants: A Synthetic Data System](https://medium.com/@atomicguy/simulants-a-synthetic-data-system-aa26a3099770)


## To Generate and Render a Simulant

``./run_container.sh``

(adjust output paths as needed)

This will generate a `tmp` directory and render multiple layers into it. The layers themselves can be used for training (i.e. depth map or UV maps), the image layers should be composited to create a single image.
