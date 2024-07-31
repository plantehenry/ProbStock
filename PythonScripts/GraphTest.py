from Tester import *
import matplotlib.pyplot as plt
from datetime import datetime

def single_graph(t, offset=0):
   graph_offsets(t, all_offsets=False, offsets=[offset])

def graph_offsets(t: Tester, all_offsets=True, offsets=[], total_diff = False):
    
    if all_offsets == True:
        offsets = [i for i in range(t.pred_distance)]


    all_dates = set()
    plt.figure(figsize=(10, 6))

    for off in offsets:
        dates = []
        diffs = []
        for y1, y2 in zip(t.offset_returns[off][1:], t.base_offset_returns[off][1:]):
            if not total_diff:
                diffs.append((y1[1] - y2[1])/y1[1] )
            else:
                diffs.append(y1[1] - y2[1])
            date = datetime.strptime(y1[0], '%Y-%m-%d')
            dates.append(date)
            all_dates.add(date)
        sorted_data = sorted(zip(dates, diffs), key=lambda x: x[0])
        dates_sorted, diffs_sorted = zip(*sorted_data)
    
        plt.plot(dates_sorted, diffs_sorted, label=off)
    # Adding labels and title
    plt.xlabel('Date')
    plt.ylabel('Percent Difference')
    plt.title('Overlayed Series on the Same Graph')

    # Adding a legend
    plt.legend()

    # Display the plot
    plt.grid(True)  # Optional: Add grid lines for better readability
    all_dates = list(all_dates)
    all_dates.sort()
    plt.xticks(all_dates[::252], rotation=45, fontsize = 3)  # Optional: Rotate x-axis labels for better readability if needed
    plt.tight_layout()  # Optional: Adjust layout for better spacing
    plt.show()

def graph_total_changes(t: Tester, all_offsets=True):
    if all_offsets == True:
        offsets = [i for i in range(t.pred_distance)]


    all_dates = set()
    plt.figure(figsize=(10, 6))
    # preds = 
    diffs = []
    for off in offsets:
        

        asset_rets = t.offset_returns[off][1:]
        base_rets = t.base_offset_returns[off][1:]

        dates = [datetime.strptime(asset_rets[1][0], '%Y-%m-%d')]
        series = [0]
        total = 0

        for idx in range(1, len(asset_rets)):
            asset_change = (asset_rets[idx][1] - asset_rets[idx - 1][1]) / asset_rets[idx - 1][1]
            base_change = (base_rets[idx][1] - base_rets[idx - 1][1]) / base_rets[idx - 1][1]
            total += asset_change - base_change
            
            series.append(total)
                         #/ y1[1])
            date = datetime.strptime(asset_rets[idx][0], '%Y-%m-%d')
            diffs.append((asset_change - base_change, date))
            dates.append(date)
            all_dates.add(date)
        sorted_data = sorted(zip(dates, series), key=lambda x: x[0])
        dates_sorted, diffs_sorted = zip(*sorted_data)
    
        plt.plot(dates_sorted, diffs_sorted, label=off)


    diffs.sort()
    # print(diffs)
    # Adding labels and title
    plt.xlabel('Date')
    plt.ylabel('Percent Difference')
    plt.title('Overlayed Series on the Same Graph')

    # Adding a legend
    plt.legend()

    # Display the plot
    plt.grid(True)  # Optional: Add grid lines for better readability
    all_dates = list(all_dates)
    all_dates.sort()
    plt.xticks(all_dates[::252], rotation=45, fontsize = 3)  # Optional: Rotate x-axis labels for better readability if needed
    plt.tight_layout()  # Optional: Adjust layout for better spacing
    plt.show()
  