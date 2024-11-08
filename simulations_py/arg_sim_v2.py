from objects.simulation import Simulation
import os
import numpy as np
from time import time
import json
import argparse
import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()


def get_appts_per_week(utilization: float, patient_types: dict):
    appts_per_week = int(np.round(np.sum([v['arrival_rate'] * v['appts_needed'] for v in patient_types.values()])/utilization))
    # print(f"The approximate number of appointments per week with a utilization of {utilization} is {appts_per_week}")
    return appts_per_week

def get_kpi_run_helper(df: pd.DataFrame, kpi: int):
    if kpi == 1:
        res = df.groupby('s_val', 
                   as_index=False).agg(
                       {'age_out': lambda x: x.sum()/x.count(),
                        'age_at_ref_yrs': 'mean',
                        'age_at_discharge_yrs': 'mean'})
        res.rename(columns={'age_out': 'stat'}, inplace=True)
        res.loc[res.shape[0]] = [0, df['age_out'].sum()/df['age_out'].count(), df['age_at_ref_yrs'].mean(), df['age_at_discharge_yrs'].mean()]
        return res
    elif kpi == 2:
        res = df.groupby('s_val', 
                   as_index=False).agg(
                       {'ref_to_ax_yrs': 'mean'})
        res.rename(columns={'ref_to_ax_yrs': 'stat'}, inplace=True)
        return res
    elif kpi == 3:
        res = df.groupby('s_val', 
                   as_index=False).agg(
                       {'ref_to_ax_yrs': lambda x: x.quantile(0.1)})
        res.rename(columns={'ref_to_ax_yrs': 'stat'}, inplace=True)
        return res
    elif kpi == 4:
        res = df.groupby('s_val', 
                   as_index=False).agg(
                       {'ref_to_ax_yrs': lambda x: x.quantile(0.9)})
        res.rename(columns={'ref_to_ax_yrs': 'stat'}, inplace=True)
        return res

def get_kpi_run(dir: str, run: int, kpi: int, burn_in=True):
    run_path = os.path.join(dir, f"run_{run}.parquet")
    df = pd.read_parquet(run_path)
    if burn_in:
        df = df.loc[df['dis_epoch'] >= \
                    np.percentile(df.loc[df['wlist_flush']==False, 'dis_epoch'], 20)].copy()
    df['ref_to_ax_yrs'] = (df['ax_epoch'] - df['ref_epoch'])/52
    df['age_at_ref_yrs'] = df['age_at_ref']/52
    df['age_at_discharge_yrs'] = (df['dis_epoch'] - df['ref_epoch'])/52 + df['age_at_ref_yrs']
    return get_kpi_run_helper(df, kpi)

def get_kpi_summary_helper(res: pd.DataFrame, n_runs: int):
    summary = res.groupby('s_val', as_index=False).agg({'stat': ['mean', 'std']})
    summary.columns = summary.columns.droplevel()
    summary.columns = ['s_val', 'mean', 'std']
    summary['sem'] = summary['std']/np.sqrt(len(res))
    summary['n_runs'] = n_runs
    return summary

def get_kpi_summary(dir: str, kpi: int, n_runs: int, burn_in=True):
    valid_responses = {1: 'age_out', 2: 'wait_time_mean', 3: 'wait_time_25', 4: 'wait_time_75'}
    results = pd.DataFrame()
    for run in range(n_runs):
        results = pd.concat([results, get_kpi_run(dir, run, kpi, burn_in)])
    summary = get_kpi_summary_helper(results, n_runs)
    return summary

if __name__ == "__main__":
    # define the argparser
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", "-r", type=int, required=True, default=1, help="Run number.")
    parser.add_argument("--utilization", "-u", type=float, required=True, default=1.2, help="Utilization of the system.")
    parser.add_argument("--n_runs", "-n", type=int, required=True, default=5, help="Number of runs.")
    parser.add_argument("--epochs", "-e", type=int, required=True, default=1000, help="Number of epochs.")
    parser.add_argument("--wait_flag", "-w", type=bool, default=False, help="Flag for wait time effect.")
    parser.add_argument("--priority_wlist", "-p", type=bool, default=False, help="Flag for priority waitlist.")
    parser.add_argument("--priority_order", "-po", nargs='+', default=[1,2,3], help="Priority order for waitlist.")
    parser.add_argument("--sim_name", "-sn", type=str, default="arg_sim", help="Name of the simulation.")
    parser.add_argument("--pct_face", "-pf", nargs='+', type=float, default=[1.0, 1.0, 1.0], help="Percentage of face-to-face treatment for each class.")
    parser.add_argument("--cancel", "-c", type=bool, default=False, help="Flag for cancellation behaviour.")
    parser.add_argument("--output_path", "-o", type=str, required=True,
                        default="../sim_summary/arg_sim", help="Output path for simulation results.")
    args = parser.parse_args()

    run_index = args.run

    # check if the output path exists
    output_path = args.output_path + f"_{run_index}.parquet"

    # define the client types
    patient_types = {1: {'arrival_rate': 5, 'appts_needed': 7},
                 2: {'arrival_rate': 13, 'appts_needed': 10},
                 3: {'arrival_rate': 6, 'appts_needed': 13}}
    # get the appts per week from user passed utilization
    appts_per_week = get_appts_per_week(args.utilization, patient_types)

    # set the number of runs
    n_runs = args.n_runs
    epochs = args.epochs
    # set the wait flag
    wait_flag = args.wait_flag
    # set the priority waitlist flag
    priority_wlist = args.priority_wlist
    priority_order = [int(i) for i in args.priority_order]

    print(f"Starting simulation run {run_index}")

    # modify the modality policy
    # print(args.pct_face)
    # mod_df = pd.DataFrame({'s_val': [1, 2, 3], 'pct_face': [float(i) for i in args.pct_face]})
    # mod_df = pd.DataFrame(np.array([[1, 2, 3],
    #                        [float(i) for i in args.pct_face]]).T, columns=['s_val', 'pct_face'])
    # mod_df.to_csv("./parametrization_data/pct_face_policy.csv", index=False)
    pct_face_policy = {
        int(i): float(j) for i, j in zip([1,2,3], args.pct_face)
    }

    # define sim name
    sim_name = args.sim_name + f"_{run_index}"

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
        # print(f"Running simulation {i}")
        start = time()
        # initialize the simulation
        sim = Simulation(appts_per_week, 4, 52*4.5, priority_wlist=priority_wlist, patient_types=patient_types, wait_flag=wait_flag,
                         priority_order=priority_order, cancellation=args.cancel)
        # create output directory
        if not os.path.exists(f"../sim_results/{sim_name}/run_{i}.parquet"):
            os.system(f"mkdir \"../sim_results/{sim_name}/run_{i}.parquet\"")
        output_dir = f"../sim_results/{sim_name}/run_{i}.parquet"
        os.system(f"rm -rf {output_dir}/*")
        # load parameters
        sim.fetch_modality_parametrization(
            path="/home/benja/num_appts_simulation/simulations_py/parametrization_data/pct_face_rmst.csv", interaction=False
        )
        # sim.fetch_modality_policy(
        #     path="/home/benja/num_appts_simulation/simulations_py/parametrization_data/pct_face_policy.csv"   # set to 100% in-person treatment for now
        # )
        sim.set_modality_policy(pct_face_policy)
        if args.cancel:
            sim.fetch_att_probs(
                path="/home/benja/num_appts_simulation/simulations_py/parametrization_data/att_probs.csv" # set to cancellation behaviour
            )
        else:
            sim.fetch_att_probs(
                path="/home/benja/num_appts_simulation/simulations_py/parametrization_data/att_probs_no_canc.csv" # set to no cancellation behaviour for now
            )
        # run simulation
        sim.run_simulation(epochs, output_dir)
        end = time()
        # print(f"Simulation runtime: {end-start:.2f}s.")

    # save simulation results to multisheet excel file
    # get the summary and add parametrization
    summary = get_kpi_summary(f"/home/benja/num_appts_simulation/sim_results/{sim_name}", kpi=1, n_runs=n_runs)
    summary['utilization'] = args.utilization
    summary['wait_flag'] = wait_flag
    summary['priority_wlist'] = priority_wlist
    summary['priority_order'] = "".join([str(i) for i in priority_order])
    summary['cancel'] = args.cancel
    summary['run'] = run_index
    # fetch the in-person treatment policy and merge onto the summary
    # modality_policy = pd.read_csv("./parametrization_data/pct_face_policy.csv")
    # summary = pd.merge(left=summary, right=modality_policy, on='s_val', how='left')
    summary['pct_face'] = np.nan
    for i, j in enumerate([1,2,3]):
        summary.loc[summary['s_val'] == j, 'pct_face'] = args.pct_face[i]
    # save the summary to the excel file
    summary.to_parquet(output_path, index=False)
    
    print(f"Simulation run {run_index} complete.")
