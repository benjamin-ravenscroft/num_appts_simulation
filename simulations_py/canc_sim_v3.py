import subprocess
import numpy as np
import shutil
import os
import time
from itertools import permutations

# Clear the directories
shutil.rmtree("../mass_simulations/sim_summary")
shutil.rmtree("../mass_simulations/sim_results")
os.makedirs("../mass_simulations/sim_summary")
os.makedirs("../mass_simulations/sim_results")

start = time.time()

# set step size for the pct_face policy
step = 0.25
n_cpus = 60 # set the number of processes to run simultaneously

total_sims = 3 * 6

sim_num = 0 # set counter for the simulation number
for utilization in [0.9, 1.0, 1.1]:
    for modality_effects in permutations([-0.15, 0, 0.15]):
        r = 0
        policies = [[float(i), float(j), float(k)] for i in np.arange(0, 1+step, step) for j in np.arange(0, 1+step, step) for k in np.arange(0, 1+step, step)]
        processes = []
        for i in policies:
            processes.append(subprocess.Popen(['python', 'arg_sim_v3.py', '-r', f"{r}", '-u', f"{utilization}", 
                        '-n', '5', '-e', '3000',
                        '-w', 'True', '-sn', f'sim_{sim_num}_{r}', '-pf', f"{i[0]}", f"{i[1]}", f"{i[2]}",
                        '-c', 'True', '-me', f"{modality_effects[0]}", f"{modality_effects[1]}", f"{modality_effects[2]}",
                        '-o', f"../mass_simulations/sim_summary/sim_{sim_num}_{r}"]))
            r += 1
            if len(processes) == n_cpus:
                exit_codes = [p.wait() for p in processes]
                print(f"Finished with first {r} simulations.")
                processes = []
        if len(processes) > 0:
            exit_codes = [p.wait() for p in processes]
        print(f"Finished with simulation runs {sim_num}/{total_sims}.")
        sim_num += 1

end = time.time()
print(f"Finished with all simulations.")
print(f"Time elapsed: {end - start:.2f} seconds.")