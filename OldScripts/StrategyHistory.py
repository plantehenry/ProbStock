from Logic import * 
from Dividend_Data_Frame import *

class StrategyHistoryCompiler():


    # also need to track the dividends for the baselin asset alone
    def __init__(self, baseline_asset, assets, initial_value, baseline_inital_value, offset) -> None:
        # list of dicts
        self.amts = []
        self.values = []
        self.dates = []
        self.assets = assets

        self.div_amount_stored = 0

        self.div_by_pay_date = {}

        for a in assets:
            self.div_by_pay_date[a] = {}

        self.dates.append(None)
        self.values.append(initial_value)
        initial_amts_dict = {baseline_asset: initial_value / baseline_inital_value}
        for asset in assets:
            if asset != baseline_asset:
                initial_amts_dict[asset] = 0

        self.amts.append(initial_amts_dict)

        self.strat_offset = offset

        self.cur_offset = 0

        self.baseline_asset = baseline_asset

        self.div_df = Dividend_data_frame()

    def get_value(self, asset_price_dict):
        cur_value = 0
        for asset in self.amts[-1].keys():
            cur_value += asset_price_dict[asset] * self.amts[-1][asset]
        cur_value += self.div_amount_stored
        return cur_value
    
    # note may want to take dividend at next date (or at opening price of next day (obviously not possible rigth now))
    def flush_div_pay_date(self, date, asset_price_dict):
        for asset in self.assets:
            if date in self.div_by_pay_date[asset]:
                amount = self.div_by_pay_date[asset][date]
                self.amts[-1][asset] += amount / asset_price_dict[asset]
                self.div_amount_stored -= amount

    def update_dividends(self, date):
        for asset in self.assets:
            pay_date, amount = self.div_df.get_div_by_ex_date(asset, date)
            if pay_date != None:
                self.div_by_pay_date[asset][pay_date] = amount
                self.div_amount_stored += amount

    # asset_pcts: dict of all pcts including baseline_asset
    def increment_day(self, asset_pcts, date, asset_price_dict):
        self.flush_div_pay_date(date, asset_price_dict)
        self.update_dividends(date)
        cur_value = self.get_value(asset_price_dict)
        self.dates.append(date)

        if self.cur_offset == self.strat_offset:
            cur_amts = {}
            for a in self.assets:
                cur_amts[a] = asset_pcts[a] * cur_value / asset_price_dict[a]
            self.amts.append(cur_amts)
            self.values.append(cur_value)
        else:
            self.amts.append(cur_amts[-1])
            self.values.append(cur_value)

        



