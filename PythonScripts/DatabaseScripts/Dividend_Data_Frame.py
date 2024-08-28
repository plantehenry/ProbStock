from DatabaseScripts.DataFrameCreatorTools import *

class Dividend_data_frame:

    def __init__(self) -> None:
        config_data: dict = read_config()
        path: str = config_data['path']
        aliases: list[str] = config_data["aliases"]
        div_files: list[str] = config_data["div_files"]
        self.div_data = load_div_data_by_ex_date(path, aliases, div_files)
    
    def get_div_by_ex_date(self, asset: str, date) -> tuple[str, float]:
        if date in self.div_data[asset]:
            return (self.div_data[asset][date]['payment_date'], self.div_data[asset][date]['amount'])
        else:
            return (None, 0)
        