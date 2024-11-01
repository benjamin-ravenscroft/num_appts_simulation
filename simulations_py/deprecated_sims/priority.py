from objects.simulation import Simulation
import os
import numpy as np
from time import time
import json

if __name__ == "__main__":
    # define sim name
    sim_name = "priority_wait_213"

    # define client types
    patient_types = {1: {'arrival_rate': 4.7, 'appts_needed': 7.24},
                     2: {'arrival_rate': 13.2, 'appts_needed': 10.28},
                     3: {'arrival_rate': 6.0, 'appts_needed': 12.72}}
    appts_per_week = 200
    utilization = np.sum([v['arrival_rate'] * v['appts_needed'] for v in patient_types.values()])/appts_per_week
    print(f"The approximate utilization with {appts_per_week} appointments per week is {utilization:.3f}")

    # set the number of runs
    n_runs = 5
    epochs = 1000
    # set the wait flag
    wait_flag = True
    # set the priority waitlist flag
    priority_wlist = True
    priority_order = [2,1,3]

    # create json file with simulation parameters and directories
    if not os.path.exists("../sim_results/" + sim_name):
        os.makedirs("../sim_results/" + sim_name)
    
    json_dict = {"sim_name": sim_name,
                 "patient_types": patient_types,
                 "n_runs": n_runs,
                 "epochs": epochs,
                 "appts_per_week": appts_per_week,
                 "wait_flag": wait_flag,
                 "priority_wlist": priority_wlist,
                 "priority_order": priority_order}
    with open(f"../sim_results/{sim_name}/parametrization.json", "w") as f:
        json.dump(json_dict, f)
    
    # run simulation
    for i in range(n_runs):
        print(f"Running simulation {i}")
        start = time()
        # initialize the simulation
        sim = Simulation(appts_per_week, 4, 52*4.5, priority_wlist, patient_types, wait_flag=wait_flag, priority_order=priority_order)
        # run a simulation run
        if not os.path.exists(f"../sim_results/{sim_name}/run_{i}.parquet"):
            os.system(f"mkdir \"../sim_results/{sim_name}/run_{i}.parquet\"")
        output_dir = f"../sim_results/{sim_name}/run_{i}.parquet"
        os.system(f"rm -rf {output_dir}/*")
        sim.run_simulation(epochs, output_dir)
        end = time()
        print(f"Simulation runtime: {end-start:.2f}s.")