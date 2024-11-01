import pandas as pd
import numpy as np
import os
import json

def get_parametrization_info(path: str):
        with open(os.path.join(path, "parametrization.json"), "r") as f:
            params = json.load(f)
        return params

def get_kpis_from_user():
    kpis = []
    valid_responses = {1: 'age-out', 2: 'wait_time_mean', 3: 'wait_time_25', 4: 'wait_time_75'}
    print("Please select the KPIs you would like to analyze:")
    print("1. Age-out rate\n2. Mean wait time\n3. 25th percentile wait time\n4. 75th percentile wait time")
    while True:
        k = int(input("Enter the number of the KPI you would like to add (or 0 to finish): "))
        if k == 0:
            return list(set(kpis))  # get unique values
        elif k in list(valid_responses.keys()):
            kpis.append(k)
        else:
            print("Invalid response. Please try again.")

def get_kpi_run_helper(df: pd.DataFrame, kpi: int):
    if kpi == 1:
        res = df.groupby('s_val', 
                   as_index=False).agg(
                       {'age_out': lambda x: x.sum()/x.count(),
                        'age_at_ref_yrs': 'mean',
                        'age_at_discharge_yrs': 'mean'})
        res.rename(columns={'age_out': 'stat'}, inplace=True)
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

def get_kpi_summary_helper(res: pd.DataFrame, kpi: str, save=False):
    summary = res.groupby('s_val', as_index=False).agg({'stat': ['mean', 'std']})
    summary.columns = summary.columns.droplevel()
    summary.columns = ['s_val', 'mean', 'std']
    summary['sem'] = summary['std']/np.sqrt(len(res))
    summary['n_runs'] = len(res)
    if save:
        summary.to_csv(f"../sim_results/{path}/summary_{kpi}.csv", index=False)
    return summary


def get_kpi_summary(dir: str, kpis: dict, n_runs: int, burn_in=True):
    valid_responses = {1: 'age-out', 2: 'wait_time_mean', 3: 'wait_time_25', 4: 'wait_time_75'}
    for k in kpis:
        print(f"Analyzing KPI: {valid_responses[k]}")
        results = pd.DataFrame()
        for run in range(n_runs):
            results = pd.concat([results, get_kpi_run(dir, run, k, burn_in)])
        summary = get_kpi_summary_helper(results, valid_responses[k], save=False)
        print(summary)

if __name__ == "__main__":
    path = "DNE"
    while not os.path.exists(f"../../sim_results/{path}/"):
        path = str(input("Please enter the path to the simulation output directory:"))
        if not os.path.exists(f"../../sim_results/{path}/"):
            print("Invalid path. Please try again.")

    params = get_parametrization_info(f"../../sim_results/{path}")
    kpis = get_kpis_from_user()
    get_kpi_summary(f"../../sim_results/{path}", kpis, params['n_runs'])