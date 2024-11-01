from objects.simulation import Simulation
import os
import numpy as np
from time import time
import json
import argparse

def get_appts_per_week(utilization: float, patient_types: dict):
    appts_per_week = int(np.round(np.sum([v['arrival_rate'] * v['appts_needed'] for v in patient_types.values()])/utilization))
    print(f"The approximate number of appointments per week with a utilization of {utilization} is {appts_per_week}")
    return appts_per_week

if __name__ == "__main__":
    # define the argparser
    parser = argparse.ArgumentParser()
    parser.add_argument("--utilization", "-u", type=float, required=True, default=1.2, help="Utilization of the system.")
    args = parser.parse_args()

    # define the client types
    patient_types = {1: {'arrival_rate': 4.7, 'appts_needed': 7.24},
                 2: {'arrival_rate': 13.2, 'appts_needed': 10.28},
                 3: {'arrival_rate': 6.0, 'appts_needed': 12.72}}
    # get the appts per week from user passed utilization
    appts_per_week = get_appts_per_week(args.utilization, patient_types)

    # set the number of runs
    n_runs = 5
    epochs = 1000
    # set the wait flag
    wait_flag = False
    # set the priority waitlist flag
    priority_wlist = False

    # define sim name
    sim_name = "fcfs"

    # create json file with simulation parameters and directories
    if not os.path.exists("../sim_results/" + sim_name):
        os.makedirs("../sim_results/" + sim_name)
    
    json_dict = {"sim_name": sim_name,
                 "patient_types": patient_types,
                 "n_runs": n_runs,
                 "epochs": epochs,
                 "appts_per_week": appts_per_week,
                 "utilization": args.utilization,
                 "wait_flag": wait_flag,
                 "priority_wlist": priority_wlist}
    with open(f"../sim_results/{sim_name}/parametrization.json", "w") as f:
        json.dump(json_dict, f)
    
    # run simulation
    for i in range(n_runs):
        print(f"Running simulation {i}")
        start = time()
        # initialize the simulation
        sim = Simulation(appts_per_week, 4, 52*4.5, priority_wlist, patient_types, wait_flag=wait_flag,
                         priority_order=[1,2,3])
        # create output directory
        if not os.path.exists(f"../sim_results/{sim_name}/run_{i}.parquet"):
            os.system(f"mkdir \"../sim_results/{sim_name}/run_{i}.parquet\"")
        output_dir = f"../sim_results/{sim_name}/run_{i}.parquet"
        os.system(f"rm -rf {output_dir}/*")
        # load parameters
        sim.fetch_modality_parametrization(
            path="./parametrization_data/pct_face_rmst.csv", interaction=False
        )
        sim.fetch_modality_policy(
            path="./parametrization_data/pct_face_policy.csv"
        )
        sim.fetch_att_probs(
            path="./parametrization_data/att_probs_no_canc.csv"
        )
        # run simulation
        sim.run_simulation(epochs, output_dir)
        end = time()
        print(f"Simulation runtime: {end-start:.2f}s.")