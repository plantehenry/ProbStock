import yaml
import pandas as pd
import numpy as np
from scipy.stats import multivariate_normal

class Pred:
    def __init__(self, config_file):
        config_data = self.read_config(config_file)
        self.not_to_use = config_data['not_to_use']
        self.aliases_to_use = config_data['aliases_to_use']
        self.baseline_asset = config_data['baseline_asset']
        self.times_to_use = config_data['times_to_use']
        self.pred_distance = config_data['pred_distance']
        self.database_file_path = config_data['database_file_path']
        self.asset_to_test = config_data['asset_to_test']
        self.results_file_path = config_data['results_file_path']
        self.test_data_years = config_data['test_data_years_back']
        self.start_year = config_data['start_year']
        self.end_year = config_data['end_year']
        self.diff=config_data['diff']

        self.df_data = self.get_df(self.database_file_path)
        self.get_columns()
        self.df_data = self.df_data[self.columns_to_use]
        
        self.results = {}
        self.results_list = []

        # yearly results
        self.diff_total = 0
        self.year_not_worked = []  
        self.years_pos = 0
        self.years_neg = 0


        self.preds = {}
        self.actuals = {}
        self.raw_assets = {}
        self.raw_baselines = {}
        self.dates = {}


        self.df_res = None
        #columns not nessesarily in this order = ['Date', 'Pred', 'Actual', "Raw_Asset", "Raw_Baseline"]
        self.generate_preds()

        # self.offset_returns = {}
        # self.base_offset_returns = {}
        # self.current_offset = 0
        # self.simulate_continous()


    def read_config(self, config_file):
        with open(config_file + '.yaml', 'r') as file:
            yaml_data = yaml.safe_load(file)
        return yaml_data
    
    def get_df(self, file_path):
        df = pd.read_csv(file_path)
        return df
    
    def get_pred_by_date(self, date):
        return self.df_res.loc[self.df_res['Date'] == date, "Pred"]
    
    def get_columns(self):
        self.columns_to_use = ["Date"]  
        for a in self.aliases_to_use:
            for t in self.times_to_use:
                new_col = ""
                if not self.diff:
                    new_col = a + "_-" + str(t) + "_dys"
                elif self.diff:
                    new_col = a + "_" + self.baseline_asset + "_-" + str(t) + "_dys_diff"
                if new_col not in self.not_to_use and not(self.diff and a == self.baseline_asset):
                    self.columns_to_use.append(new_col)
        for a in self.aliases_to_use:
            if a != self.baseline_asset:
                new_col = a + "_" + self.baseline_asset + "_" + str(self.pred_distance) + "_dys_diff"
                self.columns_to_use.append(new_col)
            new_col = a + "_" + str(self.pred_distance) + "_dys"
            self.columns_to_use.append(new_col)

    def get_rv(self, df_train):
        valid_cols = []
        for col in df_train.columns:
            if not col in self.aliases_to_use and col != "Date" and "-" in col:
                valid_cols.append(col)

        valid_cols.append(None)
        
        valid_cols[-1] = (self.asset_to_test + "_" + self.baseline_asset + "_" + str(self.pred_distance) + "_dys_diff")

        cov_mat = df_train[valid_cols]
        cov_mat = cov_mat.cov()
        cov_mat = cov_mat.to_numpy()

        # means of values
        means = []
        for col in valid_cols:
            means.append(np.mean(df_train[col]))

        rv = multivariate_normal(mean=means, cov=cov_mat, allow_singular=True)
        return rv
        

    def predict(self, inputs, rv):
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
    def get_preds_raw(self, df_test, df_train):
        data= {
            "Pred" :[],
            "Actual" : [],
            "Raw_Asset" : [],
            "Raw_Baseline" :[],
            "Date" : []
        }

        rv = self.get_rv(df_train)

        pred_columns = []
        for col_idx, col in enumerate(df_test.columns):
            if not col in self.aliases_to_use and col != "Date" and "-" in col:
                pred_columns.append(col_idx)      
    
        for idx, row in df_test.iterrows():
            
            data["Date"].append(row["Date"])

            col_name = self.asset_to_test + "_" + self.baseline_asset  + "_" + str(self.pred_distance) + "_dys_diff"
            actual = row[col_name]
            data["Actual"].append(actual)
            
            raw_asset = row[self.asset_to_test + "_" + str(self.pred_distance) + "_dys"]
            data["Raw_Asset"].append(raw_asset)

            raw_baseline = row[self.baseline_asset + "_" + str(self.pred_distance) + "_dys"]
            data["Raw_Baseline"].append(raw_baseline)

            pred_input = df_test.iloc[idx, pred_columns]
            pred = None
            if not pred_input.isnull().any():
                pred = self.predict(pred_input.tolist(), rv, )
            else:
                print(pred_input)
            data["Pred"].append(pred)

        year_df = pd.DataFrame(data)
        return year_df

    def generate_preds(self):
        dfs = []
        for year in range(self.start_year, self.end_year + 1):
            try:
                df_train = self.df_data[(self.df_data['Date'] >= str(year - self.test_data_years - 1) + '-01-01') & (self.df_data['Date'] < str(year) + '-01-01')]
                df_train = df_train.reset_index(drop=True) 
                df_test = self.df_data[(self.df_data['Date'] >= str(year) + '-01-01') & (self.df_data ['Date'] <= str(year) + '-12-31')]
                df_test = df_test.reset_index(drop=True)  
                dfs.append(self.get_preds_raw(df_test, df_train))
            except Exception as e:
                print(e)
                pass

        self.df_res = pd.concat(dfs, ignore_index = True)
        self.df_res= self.df_res.sort_values(by='Date')
        self.df_res["Date"] = pd.to_datetime(self.df_res["Date"])
