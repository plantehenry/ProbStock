# %matplotlib ipympl 
import pandas as pd
import csv
import datetime
import yaml
from DatabaseScripts.PATHS_DATABASE_SCRIPTS import *

def load_data(path, data_files, aliases):
    dates = {}
    for data_set_idx in range(len(data_files)):
        cur_alias = aliases[data_set_idx]
        with open(path + data_files[data_set_idx] + '.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            spamreader.__next__()
            for row in spamreader:
                try:
                    cur_date = datetime.datetime.strptime(row[0], '%m/%d/%Y').strftime("%Y-%m-%d")
                except Exception as e: 
                   continue
                
                if not cur_date in dates:
                    dates[cur_date] = {}
                    
                try:
                    dates[cur_date][cur_alias] = float(row[1])
                except:
                    print(row[1])
                    print(cur_alias)
                    print(row)
                    

    df = pd.DataFrame.from_dict(dates, orient='index')
    # df.columns = aliases
    df.reset_index(inplace=True)
    df = df.rename(columns = {'index':'Date'})
    df = df.sort_values('Date')
    df = df.reset_index(drop=True)
    return df


def load_div_data(path, aliases, div_files):
    div_data = {}
    for asset, file in zip(aliases, div_files):
        # Initialize data structure for the asset
        div_data[asset] = {"payment_date": set(), "ex_date": set(), "amount": {}}
        
        # Read CSV file into DataFrame
        if file != None:
            df = pd.read_csv(path + file + ".csv", delimiter=',', header=0)
            
            # Iterate over rows in the DataFrame
            for index, row in df.iterrows():
                # Extract relevant data
                ex_date = datetime.datetime.strptime(row["Ex/EFF Date"], '%m/%d/%Y').strftime("%Y-%m-%d")
                cash_amount = row["Cash Amount"]
                payment_date = datetime.datetime.strptime(row["Payment Date"], '%m/%d/%Y').strftime("%Y-%m-%d") 
                
                # Update div_data with extracted data
                div_data[asset]["ex_date"].add(ex_date)
                div_data[asset]["payment_date"].add(payment_date)
                div_data[asset]["amount"][ex_date] = cash_amount
       
    return div_data

# returns div data such that ex_date gives you all info
def load_div_data_by_ex_date(path, aliases, div_files):
    div_data = {}
    for asset, file in zip(aliases, div_files):
        # Initialize data structure for the asset
        div_data[asset] = {}
        
        # Read CSV file into DataFrame
        if file != None:
            df = pd.read_csv(path + file + ".csv", delimiter=',', header=0)
            
            # Iterate over rows in the DataFrame
            for index, row in df.iterrows():
                # Extract relevant data
                ex_date = datetime.datetime.strptime(row["Ex/EFF Date"], '%m/%d/%Y').strftime("%Y-%m-%d")
                cash_amount = row["Cash Amount"]
                payment_date = datetime.datetime.strptime(row["Payment Date"], '%m/%d/%Y').strftime("%Y-%m-%d") 
                
                # Update div_data with extracted data
                div_data[asset][ex_date] = {"amount": cash_amount, "payment_date": payment_date}
       
    return div_data

def get_x_days_ret(asset, df, div_data, distance, idx):
    start_idx = 0
    end_idx = 0
    
    if distance < 0:
        distance = abs(distance)
        start_idx = idx - distance
        end_idx = idx + 1
    else:
        start_idx = idx
        end_idx = idx + distance + 1
    num_shares = 1
    dollars = 0
    # plus one becasue th first day is like the night so you dont get the dividend 
    # becasue you have to hold it at the start
    for i in range(start_idx + 1, end_idx):
        if df.iloc[i]["Date"] in div_data["payment_date"]:
            num_shares += dollars / df.iloc[i][asset]
            dollars = 0
        if df.iloc[i]["Date"] in div_data["ex_date"]:
            dollars += div_data["amount"][df.iloc[i]["Date"]] * num_shares
    final_val = num_shares * df.iloc[end_idx - 1][asset] + dollars
    start_val = df.iloc[start_idx][asset]
    return (final_val - start_val) / start_val
            
                

# alters existing dataframe
# adds information about past and futur performance of asset for each day 
def add_correlaries_div(cor_assets, cor_days_out, df, div_data):
    # nested dictionary asset, days before(-) or after(+), [list of values]
    cors = {}

    for asset in cor_assets:
        cors[asset] = {}
        for days_out in cor_days_out:
            cors[asset][days_out] = []

    
    # iterate through all data points
    for idx, row in df.iterrows():
        # past data points
        for asset in cor_assets:
            for days_out in cor_days_out:
                if idx + days_out >= 0 and idx + days_out < df.shape[0] and idx > days_out and not pd.isna(row[asset]) and not pd.isna(df.iloc[idx + days_out][asset]): # check for enough data
                    # get percent change
                    time_period_change = get_x_days_ret(asset, df, div_data[asset], days_out, idx)  
                    cors[asset][days_out].append(time_period_change)
                else:
                    cors[asset][days_out].append(None)
        
    # input into data frame
    for asset in cor_assets:
        for days_out in cor_days_out:
            name = asset + "_" + str(days_out) + "_dys"
            df.insert(df.shape[1], name, cors[asset][days_out], True)
        


def add_pred_differences(distances, baseline_asset, assets, df):
    for dist in distances:
        for idx, asset in enumerate(assets):
    #       for idx2, asset2 in enumerate(assets[idx + 1: ]): if you want all differences
            if asset != baseline_asset:
                change_asset = df[asset + "_" + str(dist) + "_dys"]
                change_baseline = df[baseline_asset + "_" + str(dist) + "_dys"]
                diff = change_asset - change_baseline 
                df.insert(df.shape[1], asset + "_" + baseline_asset + "_" + str(dist) + "_dys_diff", diff, True)


def read_config():
    with open(PATH_TO_DATABASE_CONFIG, 'r') as file:
        yaml_data = yaml.safe_load(file)

    config_data = {}
    # Extract path and baseline_asset
    config_data['path'] = yaml_data['path']
    config_data["baseline_asset"] = yaml_data['baseline_asset']

    config_data["cor_days_out"] = yaml_data['cor_days_out']

    # Initialize lists for data files, div files, and aliases
    data_files = []
    div_files = []
    aliases = []

    # Extract data from YAML
    for entry in yaml_data['data']:
        aliases.append(entry['alias'])
        data_files.append(entry['file'])
        div_files.append(entry['div'])

    config_data['data_files'] = data_files
    config_data["div_files"] = div_files
    config_data["aliases"] = aliases

    return config_data

def get_idx_of_nearest_date_before(df, date):
    # df['Date'] = pd.to_datetime(df['Date'])


    # Specify the date to match
    date_to_match = date

    # Find indices where the Date is less than or equal to the specified date
    matching_indices = df.index[df['Date'] <= date_to_match]

    if not matching_indices.empty:
        # Get the last index where the condition is met
        nearest_index = matching_indices[-1]
    else:
        # If no date is found, raise an error or handle it appropriately
        nearest_index = None

    return nearest_index

def get_return(asset, distance, date):
    config_data = read_config()

    data_files = config_data["data_files"] 
    div_files = config_data["div_files"]
    aliases = config_data["aliases"]
    cor_days_out = config_data["cor_days_out"]

    path = config_data['path'] 
    baseline_asset = config_data["baseline_asset"] 

    df = load_data(path, data_files, aliases)
    df = df.query(baseline_asset + ".notnull()")
    df.reset_index(drop = True, inplace = True)
    div_data = load_div_data(path, aliases, div_files)
    # Sort DataFrame by Date
    df = df.sort_values(by='Date').reset_index(drop=True)
    idx = get_idx_of_nearest_date_before(df, date)
    return get_x_days_ret(asset, df, div_data[asset], distance, idx)


def create_df():
    config_data = read_config()

    data_files = config_data["data_files"] 
    div_files = config_data["div_files"]
    aliases = config_data["aliases"]
    cor_days_out = config_data["cor_days_out"]

    path = config_data['path'] 
    baseline_asset = config_data["baseline_asset"] 

    df = load_data(path, data_files, aliases)
    df = df.query(baseline_asset + ".notnull()")
    df.reset_index(drop = True, inplace = True)
    div_data = load_div_data(path, aliases, div_files)
    add_correlaries_div(aliases, cor_days_out, df, div_data)
    add_pred_differences(cor_days_out, baseline_asset, aliases, df)
    df.to_csv('../Data/AllData.csv', index=False)
