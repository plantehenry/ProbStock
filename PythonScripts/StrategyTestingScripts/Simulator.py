from Pred import *
import pandas as pd
from Logic import *
from SimulatorHelperClasses import StrategyCompoenentContainer
from SimulatorHelperClasses import PctHistory
from SimulatorHelperClasses import PctHistoryStorageByIndex
from SimulatorHelperClasses import AssetPriceDictStorageByIndex
from StrategyRunner import StrategyRunner
from DatabaseScripts.Dividend_Data_Frame import Dividend_data_frame
import math
from PATHS_STRATEGY_TESTING_SCRIPTS import *

class Simulator():

    def __init__(self, config_file, years_override=[1993, 2023]):


        self.start_year = years_override[0]
        self.end_year = years_override[1]
        self.strategies: list[StrategyDescriber] = []

        config_data = self.read_strategy(config_file)
        strats_list = config_data["Strategy"]
        self.all_data_path = config_data["AllDataPath"]
        self.initalize_strategies(strats_list)
        self.all_data = self.load_all_data()
        self.date_list = self.get_dates()
        self.assets = config_data['Assets']
        self.baseline_asset = config_data['BaselineAsset']
        self.inital_value = config_data["InitialValue"]
        self.asset_price_dict_storage: AssetPriceDictStorageByIndex = None
        self.strat_runner: StrategyRunner = None

    def read_strategy(self, config_file):
        with open(STRATEGY_CONFIG_FILEPATH +  config_file + '.yaml', 'r') as file:
            yaml_data = yaml.safe_load(file)
        return yaml_data
    
    def get_logic(self, logic: Logic, logic_vars: list):
        if logic == "BasicOne":
            return BasicOne(logic_vars)
        else:
            return AlwaysZero(logic_vars)

    def initalize_strategies(self, strats):
        for strat in strats:
            cur_logic: str = strat["logic_type"]
            logic_vars: list = strat['logic_vars']
            logic_obj: Logic = self.get_logic(cur_logic, logic_vars)
            pred_objs: list[Pred] = [Pred(SUBSTRATEGY_CONFIG_FILEPATH + p) for p in strat['file_path_for_pred_configs']]
            days_to_hold: int = strat['days_to_hold']
            asset: str = strat['asset_to_hold']
            self.strategies.append(StrategyDescriber(pred_objs, logic_obj, days_to_hold, asset))

    def load_all_data(self):
        df = pd.read_csv(self.all_data_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    
    def get_dates(self):
        self.all_data = self.all_data[(self.all_data['Date'].dt.year >= self.start_year) 
                                      & (self.all_data['Date'].dt.year <= self.end_year)]
        date_list = self.all_data['Date'].tolist()
        sorted_date_list = sorted(date_list)
        sorted_date_list = [ts.strftime('%Y-%m-%d') for ts in sorted_date_list]
        return sorted_date_list

    def get_values_list(self) -> list[float]:
        return [x[1] for x in self.strat_runner.get_values_history().get_full_list()]

    def get_last_value(self) -> float:
        return self.strat_runner.get_values_history().get_last_value()
    
    def get_amounts_list(self) -> list[tuple[int, dict[str, float]]]:
        return self.strat_runner.get_amounts_history().get_full_list()

    def simulate(self) -> None:
        pct_history_storage: PctHistoryStorageByIndex
        StrategyCompoenentContainers: StrategyCompoenentContainer 
        div_df: Dividend_data_frame = Dividend_data_frame()
        pct_history_storage, StrategyCompoenentContainers= self.get_pct_histories_and_strategy_compenent_containers(div_df)
        self.asset_price_dict_storage = self.get_asset_price_dicts()
        self.strat_runner = StrategyRunner(StrategyCompoenentContainers, self.inital_value, self.date_list, self.assets, self.baseline_asset, 
                                                      self.asset_price_dict_storage, pct_history_storage, div_df)
        self.strat_runner.run_through_all_dates()

    def get_pct_histories_and_strategy_compenent_containers(self, div_df: Dividend_data_frame) -> tuple[PctHistoryStorageByIndex, list[StrategyCompoenentContainer]]:
        pct_histories: PctHistoryStorageByIndex = PctHistoryStorageByIndex()
        StrategyCompoenentContainers: list[StrategyCompoenentContainer] = []
        for pct_history_idx, strategy in enumerate(self.strategies):
            pred_objs: list[Pred] = strategy.get_pred_objs()
            logic_obj: Logic = strategy.get_logic_obj()
            dys_to_hold: int = strategy.get_days_to_hold()
            asset: str = strategy.get_asset()
            scale_factor = 1.0 / dys_to_hold

            # each sub strategy will use one pct_history object and dys_to_hold amount contianers -> one for each offset
            for off in range(dys_to_hold):
                new_contianer = StrategyCompoenentContainer(asset, dys_to_hold, off, pct_history_idx, scale_factor, div_df)
                StrategyCompoenentContainers.append(new_contianer)

            pct_history: PctHistory = PctHistory()
            for global_idx, date in enumerate(self.date_list):
                preds = []
                for pred_obj in pred_objs: # one sub strategy may depend on multiple predictions
                    cur_pred = pred_obj.get_pred_by_date(date)
                    if cur_pred.any():
                        preds.append(cur_pred.iloc[0])
                    else:
                        preds.append(None)
                pct = logic_obj.get_pct(preds)
                pct_history.add_pct(global_idx, pct)
            pct_histories.add_pct_history(pct_history_idx, pct_history)

        return pct_histories, StrategyCompoenentContainers
    
    def get_asset_price_dicts(self) -> AssetPriceDictStorageByIndex:
        asset_price_dict_storage: AssetPriceDictStorageByIndex = AssetPriceDictStorageByIndex()
        for global_idx, date in enumerate(self.date_list):
            asset_price_dict: dict[str: float] = {}
            for asset in self.assets:
                asset_price: float = self.all_data.loc[self.all_data['Date'] == date][asset].values[0]
                if not math.isnan(asset_price):
                    asset_price_dict[asset]= asset_price
                else:
                    # maybe should be 0 but also should never be called?
                    asset_price_dict[asset] = 1 
            asset_price_dict_storage.add_asset_price_dict(global_idx, asset_price_dict)
        return asset_price_dict_storage
    
    def retrieve_asset_price_dicts(self) -> AssetPriceDictStorageByIndex:
        return self.asset_price_dict_storage

class StrategyDescriber:

    def __init__(self, pred_objs: list[Pred], logic_obj: Logic, days_to_hold: int, asset: str) -> None:
        self.pred_objs: Pred = pred_objs
        self.logic_obj: Logic = logic_obj
        self.days_to_hold: int = days_to_hold
        self.asset: str = asset

    def get_pred_objs(self) -> list[Pred]:
        return self.pred_objs

    def get_logic_obj(self) -> Logic:
        return self.logic_obj
    
    def get_days_to_hold(self) -> int:
        return self.days_to_hold
    
    def get_asset(self) -> str:
        return self.asset
    