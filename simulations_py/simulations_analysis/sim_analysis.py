"""Python script to analyze the results of a given simulation.
Will take as input the output directory of the simulation which contains:
    1. The parametrization of the simulation
    2. The output of the simulation
"""

import pandas as pd
import numpy as np
import os
import json

class SimulationAnalysis():
    def __init__(self, path: str):
        self.path = path
        self.params = self.get_parametrization_info(path)
        self.kpis = self.get_kpis_from_user()
        self.kpi_data = self.get_kpis(self.kpis)
    
    def get_parametrization_info(self, path: str):
        with open(os.path.join(path, "parametrization.json"), "r") as f:
            params = json.load(f)
        return params
    
    def get_kpis_from_user(self):
        kpis = []
        valid_responses = {1: 'age-out'}
        print("Please select the KPIs you would like to analyze:")
        print("1. Age-out rate")
        while True:
            k = int(input("Enter the number of the KPI you would like to add (or 0 to finish): "))
            if k == 0:
                return list(set(kpis))  # get unique values
            elif k in list(valid_responses.keys()):
                kpis.append(valid_responses[k])
            else:
                print("Invalid response. Please try again.")
    
    def get_run_kpi(self, dir: str, run: int, kpi: str, burn_in=True):
        run_path = os.path.join(dir, f"run_{run}.parquet")
        df = pd.read_parquet(run_path)
        if burn_in:
            df = df.loc[df['dis_epoch'] >= \
                        np.percentile(df.loc[df['wlist_flush']==False, 'dis_epoch'], 20)].copy()
        df['ref_to_ax_yrs'] = (df['ax_epoch'] - df['ref_epoch'])/52
        df['age_at_ref_yrs'] = df['age_at_ref']/52
        df['age_at_discharge_yrs'] = (df['dis_epoch'] - df['ref_epoch'])/52 + df['age_at_ref_yrs']
        return self.get_kpi_run_helper(df, kpi)
    
    def get_kpi_run_helper(self, df: pd.DataFrame, kpi: str):
        if kpi == "age-out":
            res = df.groupby('s_val', 
                       as_index=False).agg(
                           {'age_out': lambda x: x.sum()/x.count(),
                            'age_at_ref_yrs': 'mean',
                            'age_at_discharge_yrs': 'mean'})
            return res
        elif kpi == "age-out-n":
            res = df.groupby('s_val', 
                       as_index=False).agg(
                           {'age_out': 'sum',
                            'age_at_ref_yrs': 'mean',
                            'age_at_discharge_yrs': 'mean'})
            return res
        else:
            raise ValueError("KPI not yet implemented.")
        
    def get_kpis(self, kpis: list, burn_in=True):
        results = {k: pd.DataFrame() for k in kpis}
        for run in range(self.params['n_runs']):
            for k in kpis:
                results[k] = pd.concat([results[k], self.get_run_kpi(self.path, run, k, burn_in=burn_in)], axis=0)
        return results
    
    def get_kpi_summary(self, kpi: str):
        if kpi == "age-out":
            return self.get_kpi_summary_age_out()
        else:
            raise ValueError("KPI not yet implemented.")
    
    def get_kpi_summary_age_out(self, save=False):
        res = self.kpi_data['age-out']
        summary = res.groupby('s_val', as_index=False).agg({'age_out': ['mean', 'std']})
        summary.columns = summary.columns.droplevel()
        summary.columns = ['s_val', 'mean', 'std']
        summary['sem'] = summary['std']/(self.params['n_runs']**0.5)
        summary['n_sim'] = self.params['n_runs']
        print(summary)
        if save:
            summary.to_parquet(os.path.join(self.path, "age_out_summary.parquet"), index=False)
        return
    
if __name__ == "__main__":
    path = "DNE"
    while not os.path.exists(f"../../sim_results/{path}/"):
        path = str(input("Please enter the path to the simulation output directory:"))
        if not os.path.exists(f"../../sim_results/{path}/"):
            print("Invalid path. Please try again.")

    sim = SimulationAnalysis(path=f"../../sim_results/{path}/")
    sim.get_kpi_summary_age_out(save=True)
        

        
                
            
        
        
