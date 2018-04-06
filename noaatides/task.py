import datetime
import logging
import time
import threading
from noaatides import predictions

logger = logging.getLogger(__name__)


class TideNow:
    def __init__(self, prev_tide, next_tide, level, time):
        self.prev_tide = prev_tide
        self.next_tide = next_tide
        self.level = level
        self.time = time

    def tide_rising(self):
        return self.next_tide.high

    def __str__(self):
        return 'prev_tide=[{}], next_tide=[{}], level={}, time={}'.format(
            str(self.prev_tide),
            str(self.next_tide),
            self.level,
            predictions.format_datetime(self.time))


class TideTask:
    def __init__(self, tide_station, tide_offset, time_range, renew_threshold):
        self.tide_station = tide_station
        self.tide_offset = tide_offset
        self.time_range = time_range
        self.renew_threshold = renew_threshold
        self.predictions = []

    def should_renew_tides(self):
        return not self.predictions or self.predictions[-1].time < datetime.datetime.utcnow() + self.renew_threshold

    def renew(self):
        now = datetime.datetime.utcnow()
        preds = predictions.request_tide_predictions(
            self.tide_station,
            now - self.time_range[0],
            now + self.time_range[1])
        self.predictions = self.tide_offset.apply_all(preds)
        logger.info('renewed tides, count=%s, first=%s, last=%s' % (
            len(self.predictions),
            predictions.format_datetime(self.predictions[0].time),
            predictions.format_datetime(self.predictions[-1].time)))

    def await_tide(self, target_time):
        while True:
            pair = predictions.find_tide_pair(self.predictions, target_time)
            if pair:
                level = predictions.tide_level(pair[0], pair[1], target_time)
                return TideNow(pair[0], pair[1], level, target_time)
            time.sleep(1)

    def await_tide_now(self):
        return self.await_tide(datetime.datetime.utcnow())

    def _run_once(self):
        try:
            if self.should_renew_tides():
                self.renew()
        except Exception:
            logger.exception('error occurred querying tide predictions')

    def _run_loop(self):
        while True:
            self._run_once()
            time.sleep(60)

    def start(self):
        t = threading.Thread(target=self._run_loop)
        t.setDaemon(True)
        t.start()


def main():
    time_offset = predictions.AdditiveOffset(datetime.timedelta(minutes=179), datetime.timedelta(minutes=131))
    level_offset = predictions.MultiplicativeOffset(0.82, 1.15)
    tide_offset = predictions.TideOffset(time_offset, level_offset)
    query_range = (datetime.timedelta(days=1), datetime.timedelta(days=7))
    renew_threshold = datetime.timedelta(days=1)
    tt = TideTask('9414290', tide_offset, query_range, renew_threshold)
    tt.start()
    tide_now = tt.await_tide_now()
    print(tide_now)


if __name__ == '__main__':
    main()
