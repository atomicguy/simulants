#!/bin/bash

docker build ./docker -t atomicguy/simulants

docker run -it --mount src="$(pwd)",target=/usr/local/src/x,type=bind atomicguy/simulants ./run_generator.sh