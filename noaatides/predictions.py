import requests
import json
import datetime
import math

URL_NOAA = 'https://tidesandcurrents.noaa.gov/api/datagetter'


class AdditiveOffset:
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def apply(self, value):
        return [self.low + value, self.high + value]

    def __str__(self):
        return 'low={}, high={}'.format(self.low, self.high)


class MultiplicativeOffset:
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def apply(self, value):
        return [self.low * value, self.high * value]

    def __str__(self):
        return 'low={}, high={}'.format(self.low, self.high)


class TideOffset:
    def __init__(self, time_offset, level_offset):
        self.time_offset = time_offset
        self.level_offset = level_offset

    def __str__(self):
        return 'time=[{}], level=[{}]'.format(self.time_offset, self.level_offset)

    def apply(self, prediction):
        n = 1 if prediction.high() else 0
        return TidePrediction(
            self.time_offset.apply(prediction.time)[n],
            self.level_offset.apply(prediction.level)[n],
            prediction.type)

    def apply_all(self, predictions):
        return [self.apply(p) for p in predictions]


class TidePrediction:
    def __init__(self, time, level, type):
        self.time = time
        self.level = level
        self.type = type

    def high(self):
        return self.type == 'H'

    def __str__(self):
        return 'time={}, level={}, type={}'.format(format_datetime(self.time), self.level, self.type)


def format_datetime(date_time):
    return date_time.strftime('%Y%m%d %H:%M')


def parse_datetime(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M')


def request_tide_predictions(station_id, utc_from, utc_to):
    """
    Center for Operational Oceanographic Products and Services
    CO-OPS API For Data Retrieval
    https://tidesandcurrents.noaa.gov/api/
    :param station_id: NOAA tide station ID
    :param utc_from: From datetime.datetime object, in UTC
    :param utc_to: To datetime.datetime object, in UTC
    :return: List of TidePrediction objects
    """
    params = {
        'station': station_id,
        'begin_date': format_datetime(utc_from),
        'end_date': format_datetime(utc_to),
        'product': 'predictions',
        'datum': 'MLLW',
        'units': 'english',
        'time_zone': 'gmt',
        'format': 'json',
        'interval': 'hilo',
    }

    res = requests.get(url=URL_NOAA, params=params)
    res.raise_for_status()
    predictions = json.loads(res.text)['predictions']
    return [TidePrediction(parse_datetime(p['t']), float(p['v']), p['type']) for p in predictions]


def find_tide_pair(predictions, time):
    prev = None
    for p in predictions:
        if prev and prev.time <= time <= p.time:
            return prev, p
        prev = p


def _tide_sin(time):
    return (1 + math.sin((-0.5 + time) * math.pi)) / 2


def tide_level(tide_prev, tide_next, time_test):
    time_range = tide_next.time - tide_prev.time
    time_offset = time_test - tide_prev.time
    time_percent = time_offset.total_seconds() / time_range.total_seconds()
    level_range = tide_next.level - tide_prev.level
    return tide_prev.level + level_range * _tide_sin(time_percent)


def main():
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(days=1)
    predictions = request_tide_predictions('9414290', now - delta, now + delta)
    for p in predictions:
        print(p)

    print('-----')
    time_offset = AdditiveOffset(datetime.timedelta(minutes=179), datetime.timedelta(minutes=131))
    level_offset = MultiplicativeOffset(0.82, 1.15)
    offset = TideOffset(time_offset, level_offset)
    offset_predictions = offset.apply_all(predictions)
    for p in offset_predictions:
        print(p)

    print('-----')
    pair = find_tide_pair(offset_predictions, now)
    print(pair[0])
    print(pair[1])
    print(tide_level(pair[0], pair[1], now))


if __name__ == '__main__':
    main()
