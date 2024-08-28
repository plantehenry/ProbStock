from DatabaseScripts.Dividend_Data_Frame import Dividend_data_frame

class PctHistory():
    def __init__(self) -> None:
        self.storage: dict[int, float] = {}

    def add_pct(self, global_idx: int, pct: float) -> None:
        self.storage[global_idx] = pct

    def get_pct(self, global_idx) -> float:
        return self.storage[global_idx]

class PctHistoryStorageByIndex():
    def __init__(self) -> None:
        self.storage: dict[int, PctHistory] = {}

    def add_pct_history(self, pct_history_idx: int, pct_history: PctHistory) -> None:
        self.storage[pct_history_idx] = pct_history
    
    def get_pct_history(self, pct_history_idx: int) -> PctHistory:
        return self.storage[pct_history_idx]
    
    def get_pct(self, pct_history_idx: int, global_idx: int) -> float:
        return self.get_pct_history(pct_history_idx).get_pct(global_idx)

class AssetPriceDictStorageByIndex():
    def __init__(self) -> None:
        self.storage: dict[int, dict[str, float]] = {}

    def add_asset_price_dict(self, global_idx: int, asset_price_dict: dict[str, float]) -> None:
        self.storage[global_idx] = asset_price_dict
    
    def get_asset_price_dict(self, global_idx: int) -> dict[str, float]:
        return self.storage[global_idx]
    
class StrategyCompoenentContainer:
    def __init__(self, asset: str, total_offset: int, offset: int, pct_hist_id: str, scale_factor: float, div_df: Dividend_data_frame) -> None:
        self.asset: str = asset
        self.offset: int = offset
        self.total_offset: int = total_offset
        self.pct_hist_id: str = pct_hist_id
        self.scale_factor: float = scale_factor
        self.div_df: Dividend_data_frame = div_df
        self.dividends: list[DividendHolder] = []
        self.amts_hist: AmountsHistory = AmountsHistory()
        self.amts_hist.add_amount(-1, {self.asset: 0, "div": 0, "cash": 0})
        

    def release_divs(self, date: str) -> dict[str, float]:
        temp_div_list: list[DividendHolder] = []
        # div is the unreleased dividends
        # stock is the dividends that should be converted to stock
        # cash are the dividends that should be converted to cash
        total_div_amts: dict[str, float] = {"div": 0, "stock": 0, "cash": 0}
        for div in self.dividends:
            div_amts = div.get_div(date)
            if div_amts["stock"] == 0 and div_amts["cash"] == 0:
                temp_div_list.append(div)
                total_div_amts['div'] += div.get_amount()
            else:
                total_div_amts["stock"] += div_amts['stock']
                total_div_amts["cash"] += div_amts['cash']
        self.dividends = temp_div_list
        return total_div_amts
    
    # must be called every day by the Strategy runner
    def get_divs(self, date: str) -> float:
        pay_date, div = self.div_df.get_div_by_ex_date(self.asset, date)
        total_amount: float = div * self.amts_hist.get_last_amount()[self.asset]
        if pay_date != None:
            self.dividends.append(DividendHolder(pay_date, total_amount))
        return total_amount
        
    def update_div_and_get_amount(self, date: str) -> float:
        return self.get_divs(date)

    # must be called for every day
    def get_new_amount(self, total_value: float, asset_price_dict: dict[str, float], global_idx: int, date: str, pct_history_storage: PctHistoryStorageByIndex) -> float:
        # needs to be done first
        if global_idx % self.total_offset == self.offset:
            for div in self.dividends:
                div.set_convert_to_cash()
        
        total_div_amts: dict[str, float] = self.release_divs(date)
        # if today you determine a new amount div should be 0
        cur_amts: dict[str, float] = {self.asset: 0, "div": total_div_amts["div"], "cash": total_div_amts['cash']}
        if global_idx % self.total_offset == self.offset:
            # because you are redoing your allocation just return all dividends
            cur_amts['cash'] += total_div_amts['stock']
            pct: float = pct_history_storage.get_pct(self.pct_hist_id, global_idx)
            pct = pct * self.scale_factor * self.scale_factor
            ### DECIDE WHAT YOU ARE GOING TO DO WITH SCALE FACTOR ###
            cur_amts[self.asset] = total_value * pct / asset_price_dict[self.asset]
        else:
            additional_amt: float = total_div_amts['stock'] / asset_price_dict[self.asset]
            cur_amts[self.asset] = self.amts_hist.get_last_amount()[self.asset] + additional_amt
        self.amts_hist.add_amount(global_idx, cur_amts)
        return cur_amts
    
class AmountsHistory:
    # user of the class is responsible for making asset name consistent
    def __init__(self) -> None:
        # list[tuple(gloabl_idx, dict[asset/cash/div: amount])]
        self.storage: list[tuple[int, dict[str, float]]] = []
    
    def add_amount(self, global_idx: int, amounts_dict: dict[str, float]) -> None:
        self.storage.append((global_idx, amounts_dict))

    def get_last_amount(self, asset_type) -> float:
        return self.storage[-1][1][asset_type]

    def get_last_amount(self) -> dict[str, float]:
        return self.storage[-1][1]
    
    def get_full_list(self) -> list[tuple[int, dict[str, float]]]:
        return self.storage
    
class ValueHistory:
    # user of the class is responsible for making asset name consistent
    def __init__(self) -> None:
        # list[tuple(gloabl_idx, dict[asset/cash/div: amount])]
        self.storage: list[tuple[int, float]] = []
    
    def add_value(self, global_idx: int, value: float) -> None:
        self.storage.append((global_idx, value))

    def get_last_value(self) -> float:
        return self.storage[-1][1]
    
    def get_full_list(self) -> list[tuple[int, float]]:
        return self.storage
    
class DividendHolder:
    def __init__(self, pay_date: str, amount: float) -> None:
        self.pay_date: str = pay_date
        self.amount: float = amount
        self.convert_to_stock: bool = True

    def get_amount(self) -> float:
        return self.amount
    
    def set_convert_to_cash(self) -> None:
        self.convert_to_stock = False

    def get_convert_to_stock(self) -> bool:
        return self.convert_to_stock

    def get_div(self, cur_date: str) -> dict[str, float]:
        return_dict: dict[str, float] = {"stock": 0, "cash": 0}
        if cur_date >= self.pay_date:
            if self.convert_to_stock:
                return_dict['stock'] = self.amount
            else:
                return_dict["cash"] = self.amount 
        return return_dict
    

    
   



        


    
