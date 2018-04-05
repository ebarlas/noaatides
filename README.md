## noaatides

`noaatides` is a small, simple Python package with modules and classes for querying high tide and low tide predictions. 
It is specifically tailored for applications that need to determine the tide level at a specific moment at a
subordinate tide station, with time and level offsets from a reference tide station. 
Tide prediction data is provided by The Center for Operational Oceanographic Products and Services (CO-OPS). 
The [CO-OPS API](https://tidesandcurrents.noaa.gov/api/) provides access to tide predictions and a 
wide range of other data products, including temperature, pressure, humidity, etc.

## Installation

In the `noaatides` base directory, run the following.

```bash
pip install .
```

## Components

### `predictions` Module

The `predictions` module provides a tide prediction query interface.

#### `TidePrediction` Class

The `TidePrediction` class is the central data container. It represents a single tide maximum or minimum.

* `time` - `datetime` object
* `level` - `float` denoting height in feet, relative to MLLW (mean low low water)
* `type` - `string` denoting high tide `'H'` or low tide `'L'`

### `request_tide_predictions` Function

The `request_tide_predictions` function fetches tide predictions from the [CO-OPS API](https://tidesandcurrents.noaa.gov/api/) for
a specific tide station over a specific time period. The following snippet loads high and low tide predictions for 
San Francisco tide station `9414290` for a two day period, starting one day ago and ending one day from now.

```python
import datetime
from noaatides import predictions
now = datetime.datetime.utcnow()
one_day = datetime.timedelta(days=1)
tide_predictions = predictions.request_tide_predictions('9414290', now - one_day, now + one_day)
```

### `TideOffset` Class

The `TideOffset` class provides a way to adjust tide predictions based on time and level offsets
from a reference point. For example, the Petaluma River Upper Drawbridge tide station lags 179 minutes
behind the San Francisco tide station reference point at low tide and 131 minutes behind at high tide. 

```python
time_offset = predictions.AdditiveOffset(datetime.timedelta(minutes=179), datetime.timedelta(minutes=131))
level_offset = predictions.MultiplicativeOffset(0.82, 1.15)
offset = predictions.TideOffset(time_offset, level_offset)
offset_predictions = offset.apply_all(tide_predictions)
```

### `find_tide_pair` function

The `find_tide_pair` function accepts a list of tide predictions and a `datetime` as input and returns
a tuple with two tide predictions from the list that straddle the input time. If no such pair exists,
the function returns `None`.

```python
tide_pair = predictions.find_tide_pair(offset_predictions, now)
``` 

### `tide_level` function

The `tide_level` function accepts a pair of tide predictions and a time as input and returns a float that
denotes the tide level at the input time. The function estimates the tide level between the input anchors using 
the sine function.

```python
level = predictions.tide_level(tide_pair[0], tide_pair[1], now)
``` 

### `task` Module

The `task` module provides a utility for querying tide predictions in a background daemon thread. 
Foreground threads can query tide predictions from the background task.

### `TideTask` Class

```python
import datetime
from noaatides import predictions
from noaatides import task
time_offset = predictions.AdditiveOffset(datetime.timedelta(minutes=179), datetime.timedelta(minutes=131))
level_offset = predictions.MultiplicativeOffset(0.82, 1.15)
tide_offset = predictions.TideOffset(time_offset, level_offset)
query_range = (datetime.timedelta(days=1), datetime.timedelta(days=7))
renew_threshold = datetime.timedelta(days=1)
tt = task.TideTask('9414290', tide_offset, query_range, renew_threshold)
tt.start()
tide_now = tt.await_tide_now()
```

