#!/bin/sh

NUM_RENDERED=$(ls /usr/local/share/datasets/simulants/sequence_check/ | grep -v comp | wc -l)
NUM_COMP_SAT=$(ls /usr/local/share/datasets/simulants/sequence_check/ | grep comp | grep -v rgb | wc -l)
NUM_COMP_RGB=$(ls /usr/local/share/datasets/simulants/sequence_check/ | grep comp.rgb | wc -l)

echo "rendered: $NUM_RENDERED composed: $NUM_COMP_SAT / $NUM_COMP_RGB (SAT/RGB)"
