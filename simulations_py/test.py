from objects.simulation import Simulation
import os
import numpy as np
from time import time

if __name__ == "__main__":
    # define our patient types
    patient_types = {1: {'arrival_rate': 4.7, 'appts_needed': 7.24},
                     2: {'arrival_rate': 13.2, 'appts_needed': 10.28},
                     3: {'arrival_rate': 6.0, 'appts_needed': 12.72}}
    appts_per_week = 200
    utilization = np.sum([v['arrival_rate'] * v['appts_needed']
                         for v in patient_types.values()])/appts_per_week
    print(
        f"The approximate utilization with {appts_per_week} appointments per week is {utilization:.3f}")
    # run simulation with wait time effect and without
    priority_wlist = False  # turn on/off priority waitlist

    # test simulation
    sim = Simulation(appts_per_week, 4, 52*4.5, priority_wlist,
                     patient_types, wait_flag=True)
    sim.fetch_modality_parametrization(
        path="./parametrization_data/pct_face_rmst.csv", interaction=False
    )
    print(sim.get_modality_parametrization())

    sim.fetch_modality_parametrization(
        path="./parametrization_data/pct_face_rmst_inter.csv", interaction=True
    )
    print(sim.get_modality_parametrization())

    sim.fetch_modality_policy(
        path="./parametrization_data/pct_face_policy.csv"
    )
    print(sim.get_modality_policy())

    sim.fetch_att_probs(
        path="./parametrization_data/att_probs.csv"
    )
    print(sim.get_att_probs())

    start = time()
    # initialize the simulation
    # run a simulation run
    if not os.path.exists(f"../test.parquet"):
        os.system(f"mkdir \"../test.parquet\"")
    output_dir = f"../test.parquet"
    os.system(f"rm -rf {output_dir}/*")
    sim.run_simulation(1000, output_dir)
    end = time()
    print(f"Simulation runtime: {end-start:.2f}s.")
