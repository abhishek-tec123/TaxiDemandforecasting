# import pandas as pd
# from statsmodels.tsa.holtwinters import ExponentialSmoothing
# import matplotlib.pyplot as plt

# # Input data
# data = {
#     "2016-01-01": 49,
#     "2016-01-08": 111,
#     "2016-01-15": 51,
#     "2016-01-22": 52,
#     "2016-01-29": 71,
#     "2016-02-05": 41,
#     "2016-02-12": 70,
#     "2016-02-19": 47,
#     "2016-02-26": 33,
#     "2016-03-04": 49,
#     "2016-03-11": 45,
#     "2016-03-18": 49,
#     "2016-03-25": 87
# }

# # Convert to time series
# ts = pd.Series(data)
# ts.index = pd.to_datetime(ts.index)

# # Fit Holt-Winters (without seasonality)
# model = ExponentialSmoothing(ts, trend="add", seasonal=None)
# fit = model.fit()

# # Forecast next value
# forecast = fit.forecast(1)
# print("Next week's forecast:", forecast.iloc[0])

# # Optional: Plot the forecast
# ts.plot(label="Observed", marker='o')
# fit.fittedvalues.plot(label="Fitted", linestyle="--")
# forecast.plot(label="Forecast", marker='X', color='red')
# plt.legend()
# plt.title("Holt Linear Trend Forecast")
# plt.show()




import json
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib.pyplot as plt
import os

def get_pandas_week_freq(weekday):
    # Map short weekday to pandas week frequency string
    mapping = {
        'mon': 'W-MON',
        'tue': 'W-TUE',
        'wed': 'W-WED',
        'thu': 'W-THU',
        'fri': 'W-FRI',
        'sat': 'W-SAT',
        'sun': 'W-SUN',
    }
    return mapping.get(weekday.lower(), 'W')

def forecast_pickups(json_path, hex_id, plot=False, weekday='fri'):
    # Load JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)
    # Search all children for matching hex_id
    pickups = None
    for parent in data.values():
        children = parent.get("children", {})
        for child in children.values():
            if child.get("hex_id") == hex_id:
                pickups = child.get("pickups_by_date", {})
                break
        if pickups is not None:
            break
    if pickups is None:
        raise ValueError(f"Hex ID {hex_id} not found in data.")
    # Ensure we have enough data to forecast
    if len(pickups) < 3:
        raise ValueError(f"Not enough data points ({len(pickups)}) to forecast for hex_id {hex_id}.")
    # Create time series
    ts = pd.Series(pickups)
    ts.index = pd.to_datetime(ts.index)
    ts = ts.sort_index()
    freq = get_pandas_week_freq(weekday)
    ts = ts.asfreq(freq)
    # Fit Holt's Linear Trend Model
    model = ExponentialSmoothing(ts, trend="add", seasonal=None)
    fit = model.fit()
    forecast = fit.forecast(1)
    # Optional: Plot
    if plot:
        ts.plot(label="Observed", marker='o')
        fit.fittedvalues.plot(label="Fitted", linestyle="--")
        forecast.plot(label="Forecast", marker='X', color='red')
        plt.title(f"Holt Forecast for hex_id {hex_id}")
        plt.xlabel("Date")
        plt.ylabel("Pickup Count")
        plt.grid(True)
        plt.legend()
        plt.show()
    return round(forecast.iloc[0])

# forecast = forecast_pickups("/Users/abhishek/Desktop/Taxi Demand forecasting/src/plot/pickup_summary.json", "882a1008c9fffff", plot=False)
# print("Next week's forecasted pickup count:", forecast)
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning
warnings.simplefilter("ignore", ConvergenceWarning)

def add_forecast_to_json(json_path, output_path=None, weekday='fri'):
    with open(json_path, 'r') as f:
        data = json.load(f)
    freq = get_pandas_week_freq(weekday)
    for parent in data.values():
        children = parent.get("children", {})
        for child in children.values():
            hex_id = child.get("hex_id")
            pickups = child.get("pickups_by_date", {})
            if len(pickups) >= 3:
                ts = pd.Series(pickups)
                ts.index = pd.to_datetime(ts.index)
                ts = ts.sort_index()
                ts = ts.asfreq(freq)
                try:
                    model = ExponentialSmoothing(ts, trend="add", seasonal=None)
                    fit = model.fit()
                    forecast = fit.forecast(1)
                    child["forecast_next_week"] = round(forecast.iloc[0])
                except Exception as e:
                    child["forecast_next_week"] = None
            else:
                child["forecast_next_week"] = None
    if output_path is None:
        output_path = os.path.join(os.path.dirname(json_path), "pickup_summary_forecasted.json")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    return output_path
