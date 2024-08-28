import statistics
import matplotlib.pyplot as plt
from Simulator import Simulator
from Simulator import AssetPriceDictStorageByIndex

class StrategyAnalysis:

    def __init__(self, simulator: Simulator, base_sim: Simulator) -> None:
        self.simulator: Simulator = simulator
        self.base_sim: Simulator = base_sim
        # get rid of the first value becasue that is the -1 indexed value
        self.strategy_vals: list[float] = simulator.get_values_list()[1:]
        self.base_vals: list[float] = base_sim.get_values_list()[1:]
        self.dates: list[str] = simulator.date_list
        self.asset_price_dicts: AssetPriceDictStorageByIndex = self.simulator.retrieve_asset_price_dicts()

        self.valid_assets: set[str]
        self.amounts: dict[str, list[float]]
        self.fill_valid_assets_and_amounts()

        self.diff_history: list[float]
        self.get_diff_history()

        self.pct_by_asset: dict[str, list[float]] = self.get_pct_by_asset()

        self.ave_year_pct_diff: float
        self.stdev_year_pct_diff: float
        self.ave_year_pct_diff, self.stdev_year_pct_diff = self.get_ave_and_stdev_timestep_pct_change_difference(252)
        print(self.ave_year_pct_diff)
        print(self.stdev_year_pct_diff)

    def fill_valid_assets_and_amounts(self):
        amounts_raw: list[tuple[int, dict[str, float]]] = self.simulator.get_amounts_list()[1:]
        amounts_temp:dict[str, list[float]] = {}
        self.amounts = {}
        for asset in amounts_raw[1][1].keys():
            amounts_temp[asset] = []

        self.valid_assets = set()

        for idx in range(len(amounts_raw)):
            amount_dict = amounts_raw[idx][1]
            for asset in amount_dict.keys():
                amount = amount_dict[asset]
                if amount != 0: 
                    self.valid_assets.add(asset)
                amounts_temp[asset].append(amount)

        for asset in amounts_temp:
            if asset in self.valid_assets:
                self.amounts[asset] = amounts_temp[asset]


    # returns dates and then list of floats
    def get_diff_history(self) -> list[float]:
        self.diff_history: list[float] = [0]
        total: float = 0

        for idx in range(1, len(self.strategy_vals)):
            asset_change: float = (self.strategy_vals[idx] - self.strategy_vals[idx - 1]) / self.strategy_vals[idx - 1]
            base_change: float = (self.base_vals[idx] - self.base_vals[idx - 1]) / self.base_vals[idx - 1]
            total += asset_change - base_change  
            self.diff_history.append(total)
        return self.diff_history

    def graph_diff_history(self) -> None:
        plt.figure(figsize=(10, 6))
        plt.plot(self.dates, self.diff_history, label="Difference")
        plt.xlabel('Date')
        plt.ylabel('Percent Difference')
        plt.title('Running Percent Difference')
        plt.legend()

        # Display the plot
        plt.grid(True)  # Optional: Add grid lines for better readability
        plt.xticks(self.dates[::252], rotation=45, fontsize = 10)  # Optional: Rotate x-axis labels for better readability if needed
        plt.tight_layout()  # Optional: Adjust layout for better spacing
        plt.show()



    def get_pct_by_asset(self) -> dict[str, list[float]]:
        self.pct_by_asset = {}
        for asset in self.valid_assets:
            
            self.pct_by_asset[asset] = []
            for idx in range(len(self.amounts[asset])):
                value_of_asset: float = 0
                amount = self.amounts[asset][idx]
                if asset == 'cash' or asset == "div":
                    value_of_asset = amount
                else:
                    value_of_asset = amount * self.asset_price_dicts.get_asset_price_dict(idx)[asset]
                pct_of_asset = value_of_asset / self.strategy_vals[idx]
                self.pct_by_asset[asset].append(pct_of_asset)
        return self.pct_by_asset

    def graph_pct_by_asset(self) -> None:
        plt.figure(figsize=(10, 6))
        plt.xlabel('Date')
        plt.ylabel('Percent Of Value')
        plt.title('Running Percent Difference')

        for asset in self.valid_assets:
            plt.plot(self.dates, self.pct_by_asset[asset], label=asset)
        
        plt.legend()
        plt.grid(True)  # Optional: Add grid lines for better readability
        plt.xticks(self.dates[::252], rotation=45, fontsize = 10)  # Optional: Rotate x-axis labels for better readability if needed
        plt.tight_layout()  # Optional: Adjust layout for better spacing
        plt.show()


    # ave and then stdev
    def get_ave_and_stdev_timestep_pct_change_difference(self, days: int) -> tuple[float, float]:
        
        pct_differences: list[float] = []

        for idx in range(days, len(self.strategy_vals)):
            strat_pct_change = (self.strategy_vals[idx] - self.strategy_vals[idx - days]) / self.strategy_vals[idx - days]
            base_pct_change = (self.base_vals[idx] - self.base_vals[idx - days]) / self.base_vals[idx - days]
            pct_differences.append(strat_pct_change - base_pct_change)

        return statistics.mean(pct_differences), statistics.stdev(pct_differences)

    def get_date_list(self) -> list[str]:
        return self.dates
