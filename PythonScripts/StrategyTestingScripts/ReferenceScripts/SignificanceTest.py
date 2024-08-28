from Pred import *
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import numpy as np
import math

def one_sample_t(t : Pred, look_back = 1):

    pct_diff_asset = []
    look_back_adjusted = math.ceil(look_back/t.pred_distance)
    for off in range(t.pred_distance):
        return_array = t.offset_returns[off][1:]
        base_array = t.base_offset_returns[off][1:]
        for idx in range(look_back_adjusted, len(return_array)):
            asset_pct = (return_array[idx][1] - return_array[idx -look_back_adjusted][1])/ return_array[idx - look_back_adjusted][1]
            base_pct = (base_array[idx][1] - base_array[idx -look_back_adjusted][1])/ base_array[idx - look_back_adjusted][1]
            pct_diff_asset.append(asset_pct - base_pct)



    # Hypothetical population mean to test against
    mu_0 = 0.00000002  # You can change this to any value you want to test against
    t_statistic, p_value = stats.ttest_1samp(pct_diff_asset, mu_0)
    print("\One Sample t-test Results:")
    print(f"mean: {np.mean(pct_diff_asset)}")
    print(f"t-statistic: {t_statistic}")
    print(f"p-value: {p_value}")

    plt.hist(pct_diff_asset, bins=1057, edgecolor='black')  # Adjust bins as needed for your data
    plt.title('Histogram of Data Distribution')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.grid(True)
    # plt.xlim(-.001, .001)
    plt.xlim(-.0001 * look_back, .0001 * look_back)
    plt.show()

def independent_t(t : Pred, look_back = 1):
    base_rets = []
    asset_rets = []
    for off in range(t.pred_distance):
        return_array = t.offset_returns[off][1:]
        base_array = t.base_offset_returns[off][1:]

        look_back_adjusted = math.ceil(look_back/t.pred_distance)
        for idx in range(look_back_adjusted, len(return_array)):
            asset_pct = (return_array[idx][1] - return_array[idx - look_back_adjusted][1])/ return_array[idx - look_back_adjusted][1]
            base_pct = (base_array[idx][1] - base_array[idx -look_back_adjusted][1])/ base_array[idx - look_back_adjusted][1]
            asset_rets.append(asset_pct)
            base_rets.append(base_pct)

    # Perform independent samples t-test
    t_statistic, p_value = stats.ttest_ind(asset_rets, base_rets)

    print("\nIndependent Samples t-test Results:")
    print(f"t-statistic: {t_statistic}")
    print(f"p-value: {p_value}")


def paired_t(t : Pred, look_back = 1, yrs_dont_include=[]):
    base_rets = []
    asset_rets = []
    for off in range(t.pred_distance):
        return_array = t.offset_returns[off][1:]
        base_array = t.base_offset_returns[off][1:]

        look_back_adjusted = math.ceil(look_back/t.pred_distance)
        for idx in range(look_back_adjusted, len(return_array)):
            if str(return_array[idx][0].year) not in yrs_dont_include:
                asset_pct = (return_array[idx][1] - return_array[idx - look_back_adjusted][1])/ return_array[idx - look_back_adjusted][1]
                base_pct = (base_array[idx][1] - base_array[idx -look_back_adjusted][1])/ base_array[idx - look_back_adjusted][1]
                asset_rets.append(asset_pct)
                base_rets.append(base_pct)

    # Perform independent samples t-test
    t_statistic, p_value = stats.ttest_rel(asset_rets, base_rets)

    print("\nPaired Samples t-test Results:")
    print(f"t-statistic: {t_statistic}")
    print(f"p-value: {p_value}")

