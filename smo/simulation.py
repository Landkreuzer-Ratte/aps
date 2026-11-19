import itertools
import random
from dataclasses import dataclass

from buffer import Buffer
from dispatchers import AdmissionDispatcher, SelectionDispatcher
from event_calendar import EventCalendar
from models import EventType
from modules import AnalyticsModule, ModulePool
from source import Camera
from stats import Statistics
from views import StepView, SummaryView


@dataclass(frozen=True)
class SimulationConfig:
    cameras: int = 3  # число камер
    rate: float = 5.0  # событий в секунду от одной камеры
    modules: int = 2 # число приборов
    buffer_capacity: int = 5 # ячеек в буфере
    service_min: float = 0.02 # границы времени анализа, секунды
    service_max: float = 0.20
    request_limit: int = 1000 # сколько заявок сформировать за прогон
    seed: int = None

    def __post_init__(self):
        if self.cameras < 1 or self.modules < 1 or self.buffer_capacity < 1:
            raise ValueError('Камер, приборов и ячеек буфера должно быть не меньше 1')
        if self.rate <= 0:
            raise ValueError('Интенсивность потока должна быть больше нуля')
        if not 0 <= self.service_min <= self.service_max:
            raise ValueError('Нужно 0 <= service_min <= service_max')
        if self.request_limit < 1:
            raise ValueError('Заявок должно быть не меньше 1')


class Simulation:
    def __init__(self, config, step_mode=False):
        self._config = config
        self._rng = random.Random(config.seed)
        self._calendar = EventCalendar()
        self._buffer = Buffer(config.buffer_capacity)
        self._module_pool = ModulePool([
            AnalyticsModule(number, config.service_min, config.service_max, self._rng)
            for number in range(1, config.modules + 1)])
        self._statistics = Statistics(config.cameras)
        self._admission = AdmissionDispatcher(self._buffer, self._statistics)
        self._selection = SelectionDispatcher(self._buffer, self._module_pool, self._calendar)
        self._id_counter = itertools.count(1)
        self._cameras = self._build_cameras()
        self._step_view = None
        if step_mode:
            self._step_view = StepView(self._calendar, self._buffer,
                                       self._module_pool, self._statistics)
        self._summary_view = SummaryView()
        self._generated = 0
        for camera in self._cameras:
            camera.schedule_next()

    def _build_cameras(self):
        return [Camera(number, self._config.rate, self._calendar, self._rng, self._id_counter)
                for number in range(1, self._config.cameras + 1)]

    def run_step(self):
        """Один шаг берём ближайшее событие из календаря False, если пуст"""
        if self._calendar.is_empty():
            return False
        event = self._calendar.next()
        actions = []
        if event.type is EventType.DETECTION_ARRIVAL:
            assignments = self._handle_detection(event, actions)
        else:
            assignments = self._handle_completion(event, actions)
        for item in assignments:
            finish_time = self._module_pool.get(item.module_id).finish_time
            actions.append(f'заявка №{item.event.id} выбрана из ячейки {item.slot + 1}'
                           f'и отправлена на прибор {item.module_id}, '
                           f'конец анализа в {finish_time:.4f}')
        if self._step_view is not None:
            self._step_view.render(actions)
        return True

    def run_auto(self):
        while self.run_step():
            pass
        return self.finish()

    def finish(self):
        summary = self.summary()
        self._summary_view.render(summary)
        return summary

    def summary(self):
        return self._statistics.summary(self._calendar.now, self._module_pool.busy_times())

    def _handle_detection(self, event, actions):
        if self._generated >= self._config.request_limit:
            actions.append('генерация остановлена: набрано нужное число заявок')
            return []
        camera = self._cameras[event.camera_id - 1]
        detection = camera.generate_event()
        self._generated += 1
        self._statistics.record_generated(detection)
        actions.append(f'заявка №{detection.id} сформирована камерой {camera.id} '
                       f'({detection.signature.value}, уверенность {detection.confidence}%, '
                       f'{detection.mode.value})')
        if self._generated < self._config.request_limit:
            camera.schedule_next()
        result = self._admission.accept(detection)
        if result.evicted is not None:
            actions.append(f'заявка №{result.evicted.id} выбита из ячейки {result.slot + 1} '
                           f'и получает отказ')
        actions.append(f'заявка №{detection.id} поставлена в ячейку {result.slot + 1}')
        return self._selection.on_event_queued()

    def _handle_completion(self, event, actions):
        module = self._module_pool.get(event.module_id)
        done = module.finish()
        self._statistics.record_completed(done)
        actions.append(f'прибор {module.id} закончил заявку №{done.id} и освободился')
        return self._selection.on_module_freed()
