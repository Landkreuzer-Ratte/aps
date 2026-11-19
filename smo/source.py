from models import DayNight, DetectionEvent, Event, EventType, SignatureType


class Camera:
    def __init__(self, camera_id, rate, calendar, rng, id_counter):
        self._id = camera_id
        self._rate = rate
        self._calendar = calendar
        self._rng = rng
        self._id_counter = id_counter

    @property
    def id(self):
        return self._id

    def generate_event(self):
        rng = self._rng
        signature = rng.choices(list(SignatureType), weights=[0.4, 0.25, 0.35])[0]
        return DetectionEvent(
            event_id=next(self._id_counter),
            camera_id=self._id,
            target_x=round(rng.uniform(0, 100), 1),
            target_y=round(rng.uniform(0, 100), 1),
            signature=signature,
            confidence=rng.randint(50, 99),
            mode=rng.choice(list(DayNight)),
            perimeter_crossed=rng.random() < 0.3,
            arrived_at=self._calendar.now,
        )

    def schedule_next(self):
        # ИЗ1: пуассоновский поток, интервалы экспоненциальные
        moment = self._calendar.now + self._rng.expovariate(self._rate)
        self._calendar.schedule(Event(moment, EventType.DETECTION_ARRIVAL, camera_id=self._id))
