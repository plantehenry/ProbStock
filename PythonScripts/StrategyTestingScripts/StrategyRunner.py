from SimulatorHelperClasses import StrategyCompoenentContainer
from SimulatorHelperClasses import AmountsHistory
from SimulatorHelperClasses import ValueHistory
from SimulatorHelperClasses import AssetPriceDictStorageByIndex
from SimulatorHelperClasses import PctHistoryStorageByIndex
from SimulatorHelperClasses import DividendHolder
from DatabaseScripts.Dividend_Data_Frame import Dividend_data_frame

class StrategyRunner:

    def __init__(self, component_container_list:list[StrategyCompoenentContainer], inital_value: float, 
                 date_list: list[str], assets: list[str], baseline_asset: str, 
                 asset_price_dict_storage: AssetPriceDictStorageByIndex, 
                 pct_history_storage: PctHistoryStorageByIndex, div_df: Dividend_data_frame ) -> None:
        self.assets: list[str] = assets
        self.date_list: list[str] = date_list
        self.baseline_asset: str = baseline_asset
        self.asset_price_dict_storage: AssetPriceDictStorageByIndex = asset_price_dict_storage
        self.pct_history_storage: PctHistoryStorageByIndex = pct_history_storage
        self.div_df: Dividend_data_frame = div_df
        self.component_container_list: list[StrategyCompoenentContainer] = component_container_list
        self.amounts_history: AmountsHistory = AmountsHistory()
        self.value_history: ValueHistory = ValueHistory()
        self.initalize_amounts_history(inital_value)
        self.value_history.add_value(-1, inital_value)
        self.baseline_dividends: list[DividendHolder] = []
        self.counter = 0

    def get_baseline_amounts_dict(self) -> dict[str: float]:
        baseline_dict: dict[str, float]= {"cash": 0, "div": 0}
        for a in self.assets:
            baseline_dict[a] = 0
        return baseline_dict

    def initalize_amounts_history(self, inital_value) -> None:
        amounts_dict: dict[str, float] = self.get_baseline_amounts_dict()
        amounts_dict['cash'] = inital_value
        self.amounts_history.add_amount(-1, amounts_dict)
    
    def get_cur_value(self, asset_price_dict: dict[str, float], new_baseline_div: float, new_container_div: float) -> float:
        cur_value: float = 0
        amounts_dict: dict[str, float] = self.amounts_history.get_last_amount()
        for a in self.assets:
            cur_value += asset_price_dict[a] * amounts_dict[a]
        
        cur_value += amounts_dict['cash']
        cur_value += amounts_dict['div']
        cur_value += new_baseline_div
        cur_value += new_container_div
        self.counter += 1
        return cur_value
    
    def aggregate_amount_dicts(self, amount_dicts: list[dict[str, float]]) -> dict[str, float]:
        aggregate_dict: dict[str: float] = self.get_baseline_amounts_dict()
        for amount_dict in amount_dicts:
            for asset in amount_dict.keys():
                aggregate_dict[asset] += amount_dict[asset]
        return aggregate_dict

    # also release the baseline divs
    def update_all_component_containers_and_get_new_amounts(self, asset_price_dict: dict[str, float], global_idx: int, date: str) -> dict[str, float]:
        amount_dicts: list[dict[str, float]] = []
        for contianer in self.component_container_list:
            contianer_amounts = contianer.get_new_amount(self.value_history.get_last_value(), asset_price_dict, global_idx, date, self.pct_history_storage)
            amount_dicts.append(contianer_amounts)
        baseline_div_amounts = self.release_baseline_divs_and_get_amounts(date)
        amount_dicts.append(baseline_div_amounts)
        return self.aggregate_amount_dicts(amount_dicts)
    
    def fill_out_asset_amounts_with_baseline(self, asset_price_dict: dict[str, float], amount_dict: dict[str, float]) -> None:
        non_cash_and_baseline_value: float = 0
        for asset in amount_dict:
            if asset == 'div':
                non_cash_and_baseline_value += amount_dict[asset]
            elif asset != 'cash': # ignore cash it will go into the baseline asset
                non_cash_and_baseline_value += asset_price_dict[asset] * amount_dict[asset]
        amount_dict['cash'] = 0
        total_value: float = self.value_history.get_last_value()
        amount_dict[self.baseline_asset] = (total_value - non_cash_and_baseline_value) / asset_price_dict[self.baseline_asset]
        return amount_dict

    def get_divs(self, date: str) -> None:
        pay_date, div = self.div_df.get_div_by_ex_date(self.baseline_asset, date)
        total_amount: float = div * self.amounts_history.get_last_amount()[self.baseline_asset]
        if pay_date != None:
            self.baseline_dividends.append(DividendHolder(pay_date, total_amount))
        return total_amount

    def get_total_baseline_divs(self) -> float:
        total: float = 0
        for div in self.baseline_dividends:
            total += div.get_amount()
        return total
    
    # also makes sure dividends are up to date
    def release_baseline_divs_and_get_amounts(self, date: str) -> dict[str, float]:
        temp_div_list: list[DividendHolder] = []
        div_classifications = {'div': 0, 'cash': 0}
        for div in self.baseline_dividends:
            div_amts = div.get_div(date) # will return 0, 0 if the div is not paid yet
            # because baseline it will be put into "stock" but should be processed as cash
            if div_amts["stock"] == 0 and div_amts["cash"] == 0:
                temp_div_list.append(div)
                div_classifications['div'] += div.get_amount()
            else:
                # redundancy in case dividend get's released either way
                div_classifications['cash'] += div_amts['stock']
                div_classifications['cash'] += div_amts['cash']
        self.baseline_dividends = temp_div_list
        return div_classifications
    
    def update_and_get_new_contianer_divs(self, date: str) -> float:
        div_total: float = 0
        for container in self.component_container_list:
            div_total += container.update_div_and_get_amount(date)
        return div_total

    def run_through_all_dates(self):
        for global_idx, date in enumerate(self.date_list):
            new_baseline_div: float = self.get_divs(date)
            # new_baseline_div = 0
            new_container_divs: float = self.update_and_get_new_contianer_divs(date)
            # new_container_divs = 0
            # print(new_contianer_divs)
            asset_price_dict: dict[str, float] = self.asset_price_dict_storage.get_asset_price_dict(global_idx)
            cur_value: float = self.get_cur_value(asset_price_dict, new_baseline_div, new_container_divs)
            self.value_history.add_value(global_idx, cur_value)
            amount_dict: dict[str, float]= self.update_all_component_containers_and_get_new_amounts(asset_price_dict, global_idx, date)
            amount_dict = self.fill_out_asset_amounts_with_baseline(asset_price_dict, amount_dict)
            self.amounts_history.add_amount(global_idx, amount_dict)

    def get_final_value(self) -> float:
        return self.value_history.get_last_value()

    def get_amounts_history(self) -> AmountsHistory:
        return self.amounts_history
    
    def get_values_history(self) -> ValueHistory:
        return self.value_history



    