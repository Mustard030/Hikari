import datetime


class CountDown:
    def __init__(self, delta: datetime.timedelta):
        self.last = datetime.datetime.now()
        self.delta = delta

    def reset(self):
        self.last = datetime.datetime.now()

    def check(self):
        return datetime.datetime.now() - self.last > self.delta


count_down_to_retry = CountDown(datetime.timedelta(minutes=5))
