#!/bin/bash

echo $MULTI_SIM_PATH

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i"
#     python arg_sim.py -u $i -n 5 -e 1000 -po 1 2 3
# done

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i with wait effect"
#     python arg_sim.py -u $i -n 5 -e 1000 -w True -po 1 2 3
# done

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i with priority ordering"
#     python arg_sim.py -u $i -n 5 -e 1000 -p True -po 1 2 3
# done

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i with priority ordering and wait effects"
#     python arg_sim.py -u $i -n 5 -e 1000 -p True -po 3 2 1
# done

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i with priority ordering and wait effects"
#     python arg_sim.py -u $i -n 5 -e 1000 -p True -po 3 1 2
# done

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i with priority ordering and wait effects"
#     python arg_sim.py -u $i -n 5 -e 1000 -w True -p True -po 1 2 3
# done

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i with priority ordering and wait effects"
#     python arg_sim.py -u $i -n 5 -e 1000 -w True -p True -po 3 2 1
# done

# for i in 0.8 0.9 1.0 1.1 1.2; do
#     echo "Running simulation for u=$i with priority ordering and wait effects"
#     python arg_sim.py -u $i -n 5 -e 1000 -w True -p True -po 3 1 2
# done

# simulation for varying percentage of face-to-face appointments
# for i in 0.0 0.25 0.5 0.75 1.0; do
#     echo "Running simulation for face-to-face percentage=$i"
#     python arg_sim.py -u 1.2 -n 5 -e 1000 -w True -po 1 2 3 -pf $i $i $i
# done

# for i in 0.0 0.25 0.5 0.75 1.0; do
#     echo "Running simulation for face-to-face percentage=$i with cancellation effects"
#     python arg_sim.py -u 1.2 -n 5 -e 1000 -w True -po 1 2 3 -pf $i $i $i -c True
# done

# for i in 0.0 0.25 0.5 0.75 1.0; do
#     echo "Running simulation for face-to-face percentage=$i with cancellation effects"
#     python arg_sim.py -u 1.2 -n 5 -e 1000 -w True -p True -po 1 2 3 -pf $i $i $i -c True
# done

# for i in 0.0 0.25 0.5 0.75 1.0; do
#     echo "Running simulation for face-to-face percentage=$i with cancellation effects"
#     python arg_sim.py -u 1.2 -n 5 -e 1000 -w True -p True -po 3 2 1 -pf $i $i $i -c True
# done