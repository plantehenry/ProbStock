from Pred import *
import pandas as pd
from abc import ABC, abstractmethod
from Logic import *
import matplotlib.pyplot as plt
import csv
from CSVIMPUTER import *
from StrategyHistory import *

class Simulator(ABC):

    def __init__(self, config_file, years_override=[1993, 2023]):
        self.start_year = years_override[0]

        self.end_year = years_override[1]

        self.logic_objs = None
        self.pred_objs = None
        self.days_to_hold = None
        self.asset = None

        strats_list = self.read_strategy(config_file)["Strategy"]
        self.all_data_path = self.read_strategy(config_file)["all_data_path"]
        self.get_objects(strats_list)

        self.all_data = self.load_all_data()
        self.date_list = self.get_dates()

    @abstractmethod
    def simulate(config_file):
        pass
        
    def read_strategy(self, config_file):
        with open(config_file + '.yaml', 'r') as file:
            yaml_data = yaml.safe_load(file)
        return yaml_data
    
    def get_logic(self, logic, logic_vars):
        if logic == "Basic_One":
            return Basic_One()
        else:
            return Basic_One()

    def get_objects(self, strats):
        self.logic_objs = []
        self.pred_objs = []
        self.days_to_hold = []
        self.asset = []
        for strat in strats:
            cur_logic = strat[0]
            logic_vars = strat[1]
            self.logic_objs.append(self.get_logic(cur_logic, logic_vars))
            preds = [Pred(p) for p in strat[2]]
            self.pred_objs.append(preds)
            self.days_to_hold.append(strat[3])
            self.asset.append(strat[4])

    def load_all_data(self):
        df = pd.read_csv(self.all_data_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    def get_dates(self):
        self.all_data = self.all_data[(self.all_data['Date'].dt.year >= self.start_year) & (self.all_data['Date'].dt.year <= self.end_year)]
        date_list = self.all_data['Date'].tolist()
        sorted_date_list = sorted(date_list)
        return sorted_date_list

class Confined_simulator(Simulator):

    def __init__(self, config_file, years_override=[1990, 2023]):
        super().__init__(config_file, years_override=years_override)  

    def simulate(self):
        pct_histories, scaling_factors, assets = self.get_pcts()
        self.walk_all_dates(pct_histories, assets)
        # self.walk_the_preds(pct_histories, scaling_factors, assets)

    def get_pcts(self):
        # Iterate through all dates
        pct_histories = []
        scaling_factors = []
        assets = []

        for p_objs, logic_obj, dys_to_hold, asset in zip(self.pred_objs, self.logic_objs, self.days_to_hold, self.asset):
            # setting up data storage
            start_idx = len(pct_histories)
            for i in range(dys_to_hold):
                pct_histories.append([])
                assets.append(asset)
                scaling_factors.append(1.0/dys_to_hold)

            cur_offset = 0
            for date in self.date_list:
                preds = []
                for obj in p_objs:
                    cur_pred = obj.get_pred_by_date(date)
                    if cur_pred.any():
                        preds.append(cur_pred.iloc[0])
                    else:
                        preds.append(None)
                pct = logic_obj.get_pct(preds)
                for i in range(dys_to_hold):
                    if i == cur_offset:
                        # need to find the correct array to put it in
                        pct_histories[start_idx + i].append(pct)
                    else:
                        pct_histories[start_idx + i].append(None)
                cur_offset = (cur_offset + 1) % dys_to_hold
        return pct_histories, scaling_factors, assets
    


    # I will have to totally rework this
    # I want at each stage to make the pct off of the entire value
    # however, I will need to keep track of the individual atrategies
    # ex start with offset 10 -> I need to know the amount of the asset I have 
    # importantly including any dividend reinvestment
    # oh shit currently when dividends get reinvested they are auto reinvested in the same asset.
    # I dont want that I only want that if the pred hasnt changed 
    # this is all wrong will have to think very hard about it
    # thiking I need some sort of container for each pred ie one offset in a strategy
    # that stores the amount it has at each stage including keeping track of dividends
    # then the stategy history which will  have to change a lot
    # can aggregate all these containers together, calulate value etc
    # stragegy histor could maybe even erun the whole loop?
    def walk_all_dates(self, pct_histories, assets):
        BASELINE_ASSET = "sp"
        baseline_day_one = self.all_data.loc[self.all_data["Date"] == self.date_list[0]].iloc[0][BASELINE_ASSET]
        
        print(assets)
        assets = set(assets)
        assets.add(BASELINE_ASSET)
        assets = list(assets)
        strat_histories = []
        baseline_strat_hist = StrategyHistoryCompiler(BASELINE_ASSET, assets, 1, baseline_day_one, 0)

        for i in range(len(pct_histories)):
            strat_histories.append(StrategyHistoryCompiler(BASELINE_ASSET, assets, 1, baseline_day_one, 0))
        for idx, date in enumerate(self.date_list):
            baseline_asset_price = self.all_data.loc[self.all_data['Date'] == date][BASELINE_ASSET].values[0]
            asset_price_dict = {}

            for a in assets:
                asset_price = self.all_data.loc[self.all_data['Date'] == date][a].values[0]
                asset_price_dict[a] = asset_price
            
            # start_histories idx and pct_histories_idx are the same so can just iterate
            for pct_histories_idx, sh in enumerate(strat_histories):

                sh.increment_day(pct_histories[pct_histories_idx][idx][0], date, asset_price_dict)
                baseline_strat_hist.increment_day(0, date, asset_price_dict)
        print(StratHistories[0].values[-1]) # this could explain something?? 
        print(baseline_strat_hist.values[-1])
        # print(baseline_value[-1])


    def walk_the_preds(self, pct_histories, scaling_factors, assets):
        # next test -> look at perdent change between each day graphtest vs simulator 
        # actually I think I missed rounding on graph test version (actually code in pred's siulate) where I get the baseline change -> round that before using plus the asset change maybe
        # actually that doesnt make much sense acually it might because of floating point subtraction errors yes! that could be it 
        # I am almost certain that it is just that this doesnt take dividends into account
        # almost 100% sure
        initialize_csv("test.csv")
        BASELINE_ASSET = "sp"
        values = []
        amts = []
        baseline_value = []
        baseline_day_one = self.all_data.loc[self.all_data["Date"] == self.date_list[0]].iloc[0][BASELINE_ASSET]

        for i in range(len(pct_histories)):
            
            # basline_value and value of strategy both start at the same amount (baseline amount day one)
            values.append([baseline_day_one])
            baseline_value.append(baseline_day_one)
            # number of shares of baseline you own and number of shares of asset you own
            amts.append([(1, 0)])

        for idx, date in enumerate(self.date_list):
            baseline_asset_price = self.all_data.loc[self.all_data['Date'] == date][BASELINE_ASSET].values[0]
            baseline_value.append(baseline_asset_price)
            
            for strat_idx in range(len(pct_histories)):
                cur_asset_price = self.all_data.loc[self.all_data['Date'] == date][assets[strat_idx]].values[0]
                cur_amts = amts[strat_idx][-1]
                cur_val = cur_amts[0] * baseline_asset_price + cur_amts[1] * cur_asset_price

                values[strat_idx].append(cur_val)
                if pct_histories[strat_idx][idx] != None: #you are making a trade today
                    cur_pct = pct_histories[strat_idx][idx]
                    base_line_amt = (cur_val * (1 - cur_pct)) / baseline_asset_price
                    cur_asset_amt = (cur_val * cur_pct) / cur_asset_price
                    amts[strat_idx].append(((base_line_amt, cur_asset_amt)))
                    
                    add_value_to_first_column("test.csv", ((cur_val - baseline_asset_price) / baseline_day_one))
                else:
                    amts[strat_idx].append(amts[strat_idx][-1])
        
        # for a, val, base_val in zip(amts[0], values[0], baseline_value):
        #     print(f"{val} vs {base_val}, {a}")
        print((values[0][-1]-baseline_value[-1]) / baseline_value[-1])
        print(values[0][-1]/values[0][0])
        
        
        
        
        
        #### graphs
        
        # print(values[0][])
        # print(values[0])

        # diffs = []
        # asset_rets = values[0]
        # base_rets = baseline_value

        # dates = [i for i in range(len(base_rets))]
        # series = [0]
        # total = 0
        # for idx in range(1, len(asset_rets)):
        #     asset_change = (asset_rets[idx] - asset_rets[idx - 1]) / asset_rets[idx - 1]
        #     base_change = (base_rets[idx] - base_rets[idx - 1]) / base_rets[idx - 1]
        #     total += asset_change - base_change
            
        #     series.append(total)
        #                  #/ y1[1])
        #     date = asset_rets[idx]
        #     diffs.append(asset_change - base_change)
    
        # plt.plot(dates, series)

        # diffs.sort()
        # # print(diffs)
        # # Adding labels and title
        # plt.xlabel('Date')
        # plt.ylabel('Percent Difference')
        # plt.title('Overlayed Series on the Same Graph')

        # # Adding a legend
        # # plt.legend()

        # # Display the plot
        # plt.grid(True)  # Optional: Add grid lines for better readability
        # plt.xticks(dates[::252], rotation=45, fontsize = 3)  # Optional: Rotate x-axis labels for better readability if needed
        # plt.tight_layout()  # Optional: Adjust layout for better spacing
        # plt.show()
                    



        plt.figure(figsize=(10, 6))

        dates = []
        diffs = []
        for idx, (y1, y2) in enumerate(zip(values[0][1:], baseline_value[1:])):
            # if not total_diff:
            #     diffs.append((y1[1] - y2[1])/y1[1] )
            # else:
            diffs.append((y1 - y2) / baseline_value[1])
            dates.append(idx)
        
        plt.plot(dates, diffs)
        # Adding labels and title
        plt.xlabel('Date')
        plt.ylabel('Percent Difference')
        plt.title('Overlayed Series on the Same Graph')

        # Adding a legend


        # Display the plot
        plt.grid(True)  # Optional: Add grid lines for better readability
        plt.xticks(dates[::252], rotation=45, fontsize = 3)  # Optional: Rotate x-axis labels for better readability if needed
        plt.tight_layout()  # Optional: Adjust layout for better spacing
        plt.show()