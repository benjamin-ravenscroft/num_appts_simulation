#!/bin/bash

echo $MULTI_SIM_PATH

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i"
    python arg_sim.py -u $i -n 5 -e 1000 -po 1 2 3
done

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i with wait effect"
    python arg_sim.py -u $i -n 5 -e 1000 -w True -po 1 2 3
done

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i with priority ordering"
    python arg_sim.py -u $i -n 5 -e 1000 -p True -po 1 2 3
done

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i with priority ordering and wait effects"
    python arg_sim.py -u $i -n 5 -e 1000 -p True -po 3 2 1
done

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i with priority ordering and wait effects"
    python arg_sim.py -u $i -n 5 -e 1000 -p True -po 3 1 2
done

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i with priority ordering and wait effects"
    python arg_sim.py -u $i -n 5 -e 1000 -w True -p True -po 1 2 3
done

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i with priority ordering and wait effects"
    python arg_sim.py -u $i -n 5 -e 1000 -w True -p True -po 3 2 1
done

for i in 0.8 0.9 1.0 1.1 1.2; do
    echo "Running simulation for u=$i with priority ordering and wait effects"
    python arg_sim.py -u $i -n 5 -e 1000 -w True -p True -po 3 1 2
done