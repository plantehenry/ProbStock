import numpy as np
import pandas as pd
import yaml
from scipy.stats import multivariate_normal
import csv

# must filter to df columns that you want before
def get_rvs(baseline, df, aliases, pred_distance, print_mats=False):
    rvs = {}
    
    valid_cols = []
    for col in df.columns:
        if not col in aliases and col != "Date" and "-" in col:
            valid_cols.append(col)

    valid_cols.append(None)
    
    for asset in aliases:
        if asset != baseline:
            valid_cols[-1] = (asset + "_" + baseline + "_" + str(pred_distance) + "_dys_diff")

            cov_mat = df[valid_cols]
            cov_matrix = pd.DataFrame.cov(cov_mat)
            cov_mat = cov_mat.cov()
            cov_mat = cov_mat.to_numpy()
            if print_mats:
                print(asset)
                print(cov_matrix)


            # means of values
            means = []
            for col in valid_cols:
                means.append(np.mean(df[col]))
            if print_mats:
                print(means)

            rv = multivariate_normal(mean=means, cov=cov_mat, allow_singular=True)
            rvs[asset] = rv
    return rvs
        

def predict(asset, baseline, rv, inputs):
    mu = rv.mean  # Mean vector
    cov = rv.cov
    # Values of the two known variables
    known_values = inputs
    # Indices of the known variables
    known_indices = [i for i in range(len(inputs))]  # indices start from 0
    # Indices of the variable you want to find the expected value for
    unknown_index = [len(inputs)]  # index starts from 0
    # Compute the conditional mean and covariance
    mu_conditional = mu[unknown_index] + cov[unknown_index, known_indices] @ np.linalg.inv(cov[np.ix_(known_indices, known_indices)]) @ (known_values - mu[known_indices])
    # cov_conditional = cov[unknown_index, unknown_index] - np.dot(cov[unknown_index, known_indices], np.linalg.inv(cov[np.ix_(known_indices, known_indices)])) @ cov[np.ix_(known_indices, unknown_index)]
    # Expected value (mean) of the conditional distribution
    return mu_conditional[0]

# df needs tto only have the columns you want
# returns list of (preds differences, actual differences, percent change of asset, percent change of baseline)
def get_preds_raw(assets, baseline, pred_distance, df_test, df_train):
    rvs = get_rvs(baseline, df_train, assets, pred_distance)
    preds = {}
    actuals = {}
    raw_assets = {}
    raw_baselines = {}
    dates = []

    for asset in assets:
        if asset != baseline:
            raw_assets[asset] = []
            raw_baselines[asset] = []
            preds[asset] = []
            actuals[asset] = []
    
    pred_columns = []
    for col_idx, col in enumerate(df_test.columns):
        if not col in assets and col != "Date" and "-" in col:
            pred_columns.append(col_idx)
            
   
    for idx, row in df_test.iterrows():
        dates.append(row["Date"])
        for asset in assets:
            if asset != baseline:
                col_name = asset + "_" + baseline  + "_" + str(pred_distance) + "_dys_diff"
                actual = row[col_name]
                actuals[asset].append(actual)

                
                raw_asset = row[asset + "_" + str(pred_distance) + "_dys"]
                raw_assets[asset].append(raw_asset)

                raw_baseline = row[baseline + "_" + str(pred_distance) + "_dys"]
                raw_baselines[asset].append(raw_baseline)


                pred_input = df_test.iloc[idx, pred_columns]

                if not pred_input.isnull().any():
                    prediction = predict(asset, baseline, rvs[asset], pred_input.tolist())
                    preds[asset].append(prediction)
                else:
                    preds[asset].append(None)

    return preds, actuals, raw_assets, raw_baselines, dates

# deprecated
# df must only have columns you want in it
def simulate(df, aliases_to_use, baseline_asset, pred_distance):

    asset_results = {}
    baseline_results = {}
    for a in aliases_to_use:
        asset_results[a] = {}
        baseline_results[a] = {}

    for i in range(2006, 2023):
        try:
            
            df_test = df[(df['Date'] >= str(i) + '-01-01') & (df['Date'] <= str(i) + '-12-31')]
            df_test = df_test.reset_index(drop=True)  
            df_train = df[(df['Date'] < str(i) + '-01-01')]
            df_train = df_test.reset_index(drop=True) 
            preds, _, raw_assets, raw_baselines, _ = get_preds_raw(aliases_to_use, baseline_asset, pred_distance, df_test, df_train)

            for a in aliases_to_use:
                if a != baseline_asset :
                    
                    test_asset = a                    
                    asset_total = 0
                    base_total = 0
                    for offset in range(pred_distance):

                        count = 1
                        raw_total = 1
                        raw_base_total = 1
                        for date, pred, raw_change, base_change in zip(df_test["Date"][offset:], preds[test_asset][offset:], raw_assets[test_asset][offset:], raw_baselines[test_asset][offset:]):
                            if pred != None and not pd.isna(raw_change):
                                
                                if count == pred_distance: # or 10 ?

                                    if pred > 0:
                                        raw_total = raw_total * (10 * pred * (1 + raw_change)) + raw_total * ((1 - 10 * pred) * (1 + base_change))
                                        # print("long " + str(pred)[0:7] + " " + str(actual)[0:7]+ ": " + str(date) + ": " + str(total))
                                    if pred < 0:
                                        raw_total = raw_total * (10 * abs(pred) * (base_change - raw_change)) + raw_total * (1 + base_change)
                                        # print("shorted " + str(pred)[0:7] + " " + str(actual)[0:7] +  ": " + str(date) + ": " + str(total))
                                    # else:
                                        # total *= (1 + actual)   
                                    count = 0
                                    raw_base_total *= (1 + base_change) 

                                count += 1
                        asset_total += raw_total
                        base_total += raw_base_total
                    
                    asset_results[a][i] = asset_total / pred_distance
                    baseline_results[a][i] = base_total / pred_distance
        except Exception as e:
            print(e)
            for a in aliases_to_use:
                asset_results[a][i] = None
                baseline_results[a][i] = None
    return asset_results, baseline_results

def simulate_continous(df, aliases_to_use, baseline_asset, pred_distance, start_year, end_year, test_data_years):
    
    offset_returns = {}

    base_offset_returns = {}

    for a in aliases_to_use:
        offset_returns[a] = {}
        base_offset_returns[a] = {}
        for off in range(pred_distance):
            offset_returns[a][off] = [(None, 1)]
            base_offset_returns[a][off] = [(None, 1)]


    for i in range(start_year, end_year + 1):
        try:
            df_train = df[(df['Date'] >= str(i - test_data_years - 1) + '-01-01') & (df['Date'] < str(i) + '-01-01')]
            df_train = df_train.reset_index(drop=True) 
            df_test = df[(df['Date'] >= str(i) + '-01-01') & (df['Date'] <= str(i) + '-12-31')]
            df_test = df_test.reset_index(drop=True)  
            preds, _, raw_assets, raw_baselines, dates = get_preds_raw(aliases_to_use, baseline_asset, pred_distance, df_test, df_train)

            for a in aliases_to_use:
                if a != baseline_asset:
                    for idx, (pred, asset_change, base_change, date) in enumerate(zip(preds[a], raw_assets[a], raw_baselines[a], dates)):
                        last_value = offset_returns[a][idx % pred_distance][-1][1]
                        if pred > 0: 
                            offset_returns[a][idx % pred_distance].append((date, last_value * (10 * pred * (1 + asset_change)) + last_value * ((1 - 10 * pred) * (1 + base_change)), pred))
                            # print("long " + str(pred)[0:7] + " " + str(actual)[0:7]+ ": " + str(date) + ": " + str(total))
                        if pred < 0:
                            offset_returns[a][idx % pred_distance].append((date, last_value * (10 * abs(pred) * (base_change - asset_change)) + last_value * (1 + base_change), pred))
                            # print(f"{pred}, {date}, {asset_change}")
                            # print("shorted " + str(pred)[0:7] + " " + str(actual)[0:7] +  ": " + str(date) + ": " + str(total))
                        # else:
                            # total *= (1 + actual)   
                        last_base_value =  base_offset_returns[a][idx % pred_distance][-1][1]
                        base_offset_returns[a][idx % pred_distance].append((date, last_base_value * (1+ base_change)))
        except Exception as e:
            # print(e)
            pass

    return offset_returns, base_offset_returns

   
    
    #     rvs[i] = get_rvs(baseline_asset, df_train, aliases_to_use, pred_distance, print_mats=False)
    #     # preds, _, raw_assets, raw_baselines = get_preds_raw(aliases_to_use, baseline_asset, pred_distance, df_test, df_train)
    #     # pred_results[i] = preds
    #     # raw_results[i] = raw_assets
    #     # raw_baseline_results[i] = raw_baselines

    # df_test = df[(df['Date'] >= str(2006) + '-01-01') & (df['Date'] <= str(2022) + '-12-31')]
    # df_test = df_test.reset_index(drop=True)  

    # pred_columns = []

    # for col_idx, col in enumerate(df_test.columns):
    #     if not col in assets and col != "Date" and "-" in col:
    #         pred_columns.append(col_idx)

    # for idx, row in df_test.iterrows():
    #     year = int(row["Date"][0:4])
    #     for asset in aliases_to_use:
    #         if asset != baseline_asset:   
    #             cur_rv = rvs[year][asset]

    # pred_input = df_test.iloc[idx, pred_columns]               
    # if not pred_input.isnull().any():
    #     prediction = predict(asset, baseline, rvs[asset], pred_input.tolist())


    

        



    # for a in aliases_to_use:


def write_to_results(file_path, data):
    """
    Appends a new line of data to the results CSV file.

    :param file_path: str, the path to the CSV file
    :param new_data: dict, a dictionary with keys matching the CSV columns
    """
    # Define the CSV columns to ensure the correct order
    columns = [
        "Asset", "Correlaries", "Prediction Distance", "Corollary Distances", "Diff", 
        "Unused Corollaries",  "Years Not Worked", "Years Up", "Years Down", "Years Worked", 
        "Continuous Difference", "Average Difference", "Standard Deviation",
        "2006", "2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"
    ]

    
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writerow(data)


def get_columns(time_to_use, aliases_to_use, not_to_use, baseline_asset, pred_distance, diff=False):
    columns = ["Date"]  
    for a in aliases_to_use:
        for t in time_to_use:
            new_col = ""
            if not diff:
                new_col = a + "_-" + str(t) + "_dys"
            elif diff:
                new_col = a + "_" + baseline_asset + "_-" + str(t) + "_dys_diff"
            if new_col not in not_to_use and not(diff and a == baseline_asset):
                columns.append(new_col)
    for a in aliases_to_use:
        if a != baseline_asset:
            new_col = a + "_" + baseline_asset + "_" + str(pred_distance) + "_dys_diff"
            columns.append(new_col)
        new_col = a + "_" + str(pred_distance) + "_dys"
        columns.append(new_col)

    
    return columns

def read_config():
    with open('TestConfig.yaml', 'r') as file:
        yaml_data = yaml.safe_load(file)
    return yaml_data

def get_df(file_path):
    df = pd.read_csv(file_path)
    return df


def list_to_string(l):
    if len(l) == 0:
        return ""
    
    res = ""
    for i in l:
        res += str(i) + ' ,'
    return res[:len(res) - 2]

def run_test():
    config_data = read_config()
    not_to_use = config_data['not_to_use']
    aliases_to_use = config_data['aliases_to_use']
    baseline_asset = config_data['baseline_asset']
    times_to_use = config_data['times_to_use']
    pred_distance = config_data['pred_distance']
    database_file_path = config_data['database_file_path']
    asset_to_test = config_data['asset_to_test']
    results_file_path = config_data['results_file_path']
    test_data_years = config_data['test_data_years_back']
    start_year = config_data['start_year']
    end_year = config_data['end_year']

    df = get_df(database_file_path)

    columns_to_use = get_columns(times_to_use, aliases_to_use, not_to_use, baseline_asset, pred_distance, diff=config_data['diff'])

    df = df[columns_to_use]

    results = {}
    results_list = []
    # yearly results
    diff_total = 0
    year_not_worked = []  
    years_pos = 0
    years_neg = 0

    for i in range(start_year, end_year):
        offset_returns, base_offset_returns = simulate_continous(df, aliases_to_use, baseline_asset, pred_distance, i, i, test_data_years) 
        
        total_ret = 0
        for off in range(pred_distance):
            total_ret += offset_returns[asset_to_test][off][-1][1]
            # print(offset_returns[asset_to_test][off])

        base_total_ret = 0
        for off in range(pred_distance):
            base_total_ret += base_offset_returns[asset_to_test][off][-1][1]

        asset_ret = total_ret/pred_distance
        base_ret = base_total_ret/pred_distance
        difference = asset_ret - base_ret
        diff_total += difference

        results[str(i)] = difference 

        if difference < 0:
            years_neg += 1
            results_list.append(difference)
        elif difference > 0: # dont include 0s
            years_pos += 1
            results_list.append(difference)
        elif difference == 0:
            year_not_worked.append(str(i))
        # print(i)
        # print(difference)

    stdev = np.std(results_list)
    average_difference = diff_total / (years_pos + years_neg)

    # continous results
    offset_returns, base_offset_returns = simulate_continous(df, aliases_to_use, baseline_asset, pred_distance, start_year, end_year, test_data_years)
    total_ret = 0
    for off in range(pred_distance):
        total_ret += offset_returns[asset_to_test][off][-1][1]

    base_total_ret = 0
    for off in range(pred_distance):
        base_total_ret += base_offset_returns[asset_to_test][off][-1][1]
    
    asset_ret = total_ret/pred_distance
    base_ret = base_total_ret/pred_distance
    continuous_diff = asset_ret - base_ret

    # build dictionary
    results["Asset"] = asset_to_test
    results["Correlaries"] = list_to_string(aliases_to_use)
    results["Prediction Distance"] = pred_distance
    results["Corollary Distances"] = list_to_string(times_to_use)
    results["Unused Corollaries"] = list_to_string(not_to_use)
    results["Years Not Worked"] = list_to_string(year_not_worked)
    results["Years Up"] = years_pos
    results["Years Down"] = years_neg
    results["Years Worked"] =  years_pos + years_neg
    results["Continuous Difference"] = continuous_diff
    results["Average Difference"] = average_difference
    results["Standard Deviation"] = stdev
    results["Diff"] = str(config_data['diff'])

    print(f"Ave Diff: {results['Average Difference']}")
    print(f"Std Dev: {results['Standard Deviation']}")


    write_to_results(results_file_path, results)



    


    # asset_results, baseline_results = simulate(df, aliases_to_use, baseline_asset, pred_distance)
    

    # for asset in sorted(asset_results.keys()):
    #     if asset != baseline_asset:
    #         print(asset)
    #         total_return = 1
    #         baseline_total_return = 1
    #         for year in sorted(asset_results[asset].keys()):
    #             difference = None
    #             if asset_results[asset][year] != None:
    #                 total_return *= asset_results[asset][year]
    #                 baseline_total_return *= baseline_results[asset][year]
    #                 difference = asset_results[asset][year] - baseline_results[asset][year]
    #             print(f"{year}: {asset_results[asset][year]}")
    #             print(f"baseline: {baseline_results[asset][year]}")
    #             print(f"differnce: {difference}")
    #             print("-------------------------")
    #         print(f"total return: {total_return}")
    #         print(f"baseline return: {baseline_total_return}")
    #         print("_________________________")



# test tool kinda unclear if working ebcause of offsett stuff so
# redo it and just take the rv from the year that your pred starts in but keep a running total from
# 2006 -2023