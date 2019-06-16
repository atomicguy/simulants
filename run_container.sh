#!/bin/bash

docker build ./docker -t atomicguy/blender

docker run -it --mount src="$(pwd)",target=/usr/local/src/x,type=bind atomicguy/blender ./run_generator.sh