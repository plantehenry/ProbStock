from TestTools import read_config
import pandas as pd
import math

def check_for_missing(config_file):
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

        