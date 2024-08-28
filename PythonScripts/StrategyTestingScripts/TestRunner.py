import sys
import os
sys.path.append(os.path.abspath('..'))
from TestTools import *
from DatabaseScripts.MissingDataCheck import *
from Simulator import *
from StrategyAnalysis import *

import pandas as pd

if __name__ == "__main__":

    sim = Simulator("Strategy", years_override=[2005, 2022])
    sim.simulate()
    sim_baseline = Simulator("BaselineStrategy", years_override=[2005,2022])
    sim_baseline.simulate()
    print(sim.get_last_value())
    print(sim_baseline.get_last_value())

    strat_analysis = StrategyAnalysis(sim, sim_baseline)


    strat_analysis.graph_pct_by_asset()
    strat_analysis.graph_diff_history()