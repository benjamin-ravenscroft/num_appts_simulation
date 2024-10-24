import pandas as pd
from scipy import stats as ss
import numpy as np

def compare_age_out_rate(sim1: pd.DataFrame, sim2: pd.DataFrame):
    for s in sim1['s_val'].unique():
        print(f"Comparing age-out rate for s_val {s}")
        sim1_s = sim1.loc[sim1['s_val'] == s]
        sim2_s = sim2.loc[sim2['s_val'] == s]
        t = (sim2_s['mean'] - sim1_s['mean'])/np.sqrt((sim2_s['std']**2/sim2_s['n_sim']) + (sim1_s['std']**2/sim1_s['n_sim']))
        t = t.values[0]
        p = 1 - ss.t.cdf(t, sim1_s['count'].iloc[0] + sim2_s['count'].iloc[0] - 2)
        print(f"The difference in means between waiting and no waiting effect is: {sim2_s['mean'].iloc[0] - sim1_s['mean'].iloc[0]:.3f}")
        print(f"The t-statistic is {t:.3f} and the p-value is {p:.3f}")

if __name__ == "__main__":
    path_to_sim1 = "../../sim_results/fcfs/"
    path_to_sim2 = "../../sim_results/fcfs_wait/"

    sim1 = pd.read_parquet(path_to_sim1 + "age_out_summary.parquet")
    sim2 = pd.read_parquet(path_to_sim2 + "age_out_summary.parquet")

    compare_age_out_rate(sim1, sim2)