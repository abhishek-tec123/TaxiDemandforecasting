# import pandas as pd
# from statsmodels.tsa.holtwinters import ExponentialSmoothing
# import matplotlib.pyplot as plt

# # Input data
# data = {
#     "2016-01-01": 8,
#     "2016-01-08": 5,
#     "2016-01-15": 4,
#     "2016-01-22": 5,
#     "2016-01-29": 4,
#     "2016-02-05": 3,
#     "2016-02-12": 7,
#     "2016-02-19": 4,
#     "2016-02-26": 1,
#     "2016-03-04": 7,
#     "2016-03-11": 4,
#     "2016-03-18": 3,
#     # "2016-03-25": 87
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

import json
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import os
# Suppress only the runtime warnings from statsmodels
warnings.filterwarnings("ignore", category=RuntimeWarning)

def add_forecast_to_json(json_path, output_path=None, weekday='fri'):
    with open(json_path, 'r') as f:
        data = json.load(f)

    freq = get_pandas_week_freq(weekday)

    for parent in data.values():
        children = parent.get("children", {})
        for child in children.values():
            hex_id = child.get("hex_id")
            pickups = child.get("pickups_by_date", {})

            if pickups:
                ts = pd.Series(pickups)
                ts.index = pd.to_datetime(ts.index)
                ts = ts.sort_index()

                # Force to weekly frequency and forward-fill missing weeks
                ts = ts.asfreq(freq)
                ts = ts.ffill()

                # Not enough data to forecast
                if ts.notna().sum() < 2:
                    child["forecast_next_week"] = None
                    child["forecast_accuracy"] = None
                    child["forecast_confidence_percent"] = None
                    continue

                try:
                    model = ExponentialSmoothing(ts, trend="add", seasonal=None)
                    fit = model.fit()
                    forecast = fit.forecast(1)
                    forecast_value = round(forecast.iloc[0])

                    # Always set forecast value if model worked
                    child["forecast_next_week"] = forecast_value

                    # Capture last observed week metrics and errors vs fitted value
                    try:
                        last_week_date = ts.index.max()
                        last_week_actual = int(ts.iloc[-1])
                        # Use fitted value corresponding to the last observed point
                        if hasattr(fit, "fittedvalues") and not pd.isna(fit.fittedvalues.iloc[-1]):
                            last_week_fitted = int(round(fit.fittedvalues.iloc[-1]))
                        else:
                            last_week_fitted = None

                        child["last_week_date"] = last_week_date.strftime("%Y-%m-%d") if pd.notna(last_week_date) else None
                        child["last_week_actual"] = last_week_actual
                        child["last_week_forecast"] = last_week_fitted

                        # Compute missed/extra rides for the targeted last week date
                        if last_week_fitted is not None:
                            diff = last_week_fitted - last_week_actual
                            missed = int(max(0, diff))  # forecast > actual
                            extra = int(max(0, -diff))  # actual > forecast
                            child["last_week_missed_rides"] = missed
                            child["last_week_extra_rides"] = extra
                        else:
                            child["last_week_missed_rides"] = None
                            child["last_week_extra_rides"] = None
                    except Exception:
                        # Be robust: if any issue, keep fields but mark as None
                        child["last_week_date"] = None
                        child["last_week_actual"] = None
                        child["last_week_forecast"] = None
                        child["last_week_missed_rides"] = None
                        child["last_week_extra_rides"] = None

                    # Historical accuracy (MAPE across entire fit)
                    fitted_values = fit.fittedvalues
                    mape_series = abs((ts - fitted_values) / ts.replace(0, float('nan'))) * 100
                    mape = mape_series.dropna().mean()

                    if pd.notna(mape):
                        mape_rounded = round(mape, 2)
                        conf_rounded = round(max(0, 100 - mape_rounded), 2)
                        child["forecast_accuracy"] = mape_rounded
                        child["forecast_confidence_percent"] = conf_rounded
                    else:
                        child["forecast_accuracy"] = None
                        child["forecast_confidence_percent"] = None

                except Exception as e:
                    print(f"Forecast failed for hex_id {hex_id}: {e}")
                    child["forecast_next_week"] = None
                    child["forecast_accuracy"] = None
                    child["forecast_confidence_percent"] = None
            else:
                child["forecast_next_week"] = None
                child["forecast_accuracy"] = None
                child["forecast_confidence_percent"] = None

    if output_path is None:
        output_path = os.path.join(os.path.dirname(json_path), "pickup_summary_forecasted.json")

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    return output_path