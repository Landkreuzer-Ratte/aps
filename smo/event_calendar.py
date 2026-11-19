import heapq
import itertools


class EventCalendar:
    def __init__(self):
        self._events = []
        self._counter = itertools.count()   # чтобы при одинаковом времени не сравнивались сами события
        self._now = 0.0

    @property
    def now(self):
        return self._now

    def schedule(self, event):
        #допустим время одинаковое, но вот счётчик одним и тем же быть не может, так что всё нормально попадает в кучу
        heapq.heappush(self._events, (event.time, next(self._counter), event))

    def next(self):
        time, _, event = heapq.heappop(self._events)
        self._now = time
        return event

    def upcoming(self):
        return [event for _, _, event in sorted(self._events)]

    def is_empty(self):
        return not self._events
