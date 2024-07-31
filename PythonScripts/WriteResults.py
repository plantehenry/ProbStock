from Tester import *
from TestTools import *

#### You need to change the storage of things in tester -> just use a dataframe or rethink it it is confising
# or you could not and just put the offset rutrns into a df in here and pull from them that way idk bro figure it out


def WriteResults(t : Tester):
    results = {}

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


def get_yearly_results(t : Tester, results):
     for i in range(t.start_year, t.end_year):
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