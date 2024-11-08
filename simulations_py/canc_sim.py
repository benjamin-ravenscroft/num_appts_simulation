import subprocess
import numpy as np
import shutil
import os
import time

# Clear the directories
shutil.rmtree("../sim_summary")
shutil.rmtree("../sim_results")
os.makedirs("../sim_summary")
os.makedirs("../sim_results")

start = time.time()

step = 0.2
n_cpus = 60 # set the number of processes to run simultaneously
r = 0
policies = [[float(i), float(j), float(k)] for i in np.arange(0, 1+step, step) for j in np.arange(0, 1+step, step) for k in np.arange(0, 1+step, step)]
processes = []
for i in policies:
    processes.append(subprocess.Popen(['python', 'arg_sim_v2.py', '-r', f"{r}", '-u', '1.2', '-n', '5', '-e', '1000',
                '-w', 'True', '-p', 'True', '-po', '1', '2', '3', '-sn', f'arg_sim_{r}', '-pf', f"{i[0]}", f"{i[1]}", f"{i[2]}",
                '-c', 'True', '-o', "../sim_summary/arg_sim"]))
    r += 1
    if len(processes) == n_cpus:
        exit_codes = [p.wait() for p in processes]
        print(f"Finished with first {r} simulations.")
        processes = []

# for i in np.arange(0, 1+step, step):
#     processes = []
#     for j in np.arange(0, 1+step, step):
#         for k in np.arange(0, 1+step, step):
#             processes.append(subprocess.Popen(['python', 'arg_sim_v2.py', '-r', f"{r}", '-u', '1.2', '-n', '5', '-e', '1000',
#                 '-w', 'True', '-p', 'True', '-po', '1', '2', '3', '-sn', f'arg_sim_{r}', '-pf', f"{i}", f"{j}", f"{k}",
#                 '-c', 'True', '-o', "../sim_summary/arg_sim"]))
#             r += 1
#     exit_codes = [p.wait() for p in processes]
#     print(f"Finished with pct_face: {i}, {j}, {[k for k in np.arange(0, 1+step, step)]}")

end = time.time()
print(f"Finished with all simulations.")
print(f"Time elapsed: {end - start:.2f} seconds.")
