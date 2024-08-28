from StrategyTestingScripts.TestTools import read_config
import pandas as pd
import math

def check_for_missing_asset_values(config_file):
    config = read_config()
    df = pd.read_csv(config["database_file_path"])
    aliases = config["aliases_to_use"]
    missing_dates = {}
    has_started = {}
    for a in aliases:
        missing_dates[a] = []
        has_started[a] = False
    for date, row in df.iterrows():
        for a in aliases:
            if math.isnan(row[a]) and has_started[a]:
                missing_dates[a].append(row["Date"])
            elif not math.isnan(row[a]):
                has_started[a] = True
    print(missing_dates)


# note reads from a specfic config file
def check_for_missing_any_value(config_file, max_year:str="2022"):
    config = read_config()
    df = pd.read_csv(config["database_file_path"])
    missing_dates = {}
    has_started = {}
    for col in df.columns:
        missing_dates[col] = []
        has_started[col] = False
    for date, row in df.iterrows():
        if row['Date'] < max_year:
            for col in df.columns:
                if col != "Date":
                    try:
                        if math.isnan(row[col]) and has_started[col]:
                            missing_dates[col].append(row["Date"])
                        elif not math.isnan(row[col]):
                            has_started[col] = True
                    except:
                        missing_dates[col].append(row["Date"])
    for col in missing_dates.keys():
        if len(missing_dates[col]) != 0:
            print(missing_dates[col])
        