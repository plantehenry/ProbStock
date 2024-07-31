# from TestTools import run_test
from Tester import Tester
from TestTools import *
from GraphTest import *
from SignificanceTest import *
from MissingDataCheck import *

import pandas as pd

if __name__ == "__main__":
    # run_test()
    config_file = "TestConfig"
    t1 = Tester(config_file)
    # graph_total_changes(t1)
    graph_offsets(t1, total_diff=True)
    graph_offsets(t1, total_diff=False)
    graph_total_changes(t1)
    # print(max(t1.preds[2002]))
    # print(t1.offset_returns)
    # one_sample_t(t1)
    # independent_t(t1)
    # paired_t(t1, look_back=1)
    # check_for_missing(config_file)


    # columns = ['Date', 'value', "pred"]

    # # Create Pandas DataFrame
    # df_test = pd.DataFrame(t1.offset_returns[0], columns=columns)
    # df_test = df_test.sort_index()

    # # Convert 'Date' column to datetime format and set as index
    # df_test['Date'] = pd.to_datetime(df_test['Date'])
    # df_test.set_index('Date', inplace=True)

    # first_test = df_test.loc['2007'].iloc[0]["value"]  # iloc[0] gets the first row
    # last_test = df_test.loc['2007'].iloc[-1]["value"]

    # diff_test = (last_test - first_test) / first_test

    # columns = ['Date', 'value']

    # df_base = pd.DataFrame(t1.base_offset_returns[0], columns=columns)
    # df_base = df_base.sort_index()

    # # Convert 'Date' column to datetime format and set as index
    # df_base['Date'] = pd.to_datetime(df_base['Date'])
    # df_base.set_index('Date', inplace=True)

    # first_base = df_base.loc['2007'].iloc[0]["value"]  # iloc[0] gets the first row
    # last_base = df_base.loc['2007'].iloc[-1]["value"]

    # diff_base = (last_base -first_base) / first_base

    # print(diff_test)
    # print(diff_base)
    # print(diff_test - diff_base)

    