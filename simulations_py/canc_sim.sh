for i in 0.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0; do
    echo "Running simulation for face-to-face percentage=$i with cancellation effects"
    python arg_sim.py -u 1.2 -n 5 -e 1000 -w True -p True -po 3 2 1 -pf $i $i $i -c True
done