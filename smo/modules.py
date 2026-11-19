class AnalyticsModule:
    """Под аналитическим модулем подразумевается некий сервер или группа серверов, в крайнем случае мощный пк(если камер мало).
    Несмотря на то, что камеры у нас умные и способны многие действия выполнить самостоятельно, из-за их ограничений
    (опасно и очень дорого ставить мощное железо в каждую камеру: они довольно часто ломаются из-за погоды и вандалов)
    достоверность данных получаемых от них оставляет желать лучшего, поэтому кмаера примерно определяет что происходит
    и стоит ли об этом сообщать, а модули уже, имея железо мощнее, быстро и качественно анализируют полученные данные и
    выносят свой вердикт + если потребуется можно добавить доп логику и действия в модули (автоматический вызов гбр по
    координатма нарушителя при попытке проникновения и/или вызов полиции/скорой при определённых ксловиях и т.д.)
    """
    def __init__(self, module_id, service_min, service_max, rng):
        self._id = module_id
        self._service_min = service_min
        self._service_max = service_max
        self._rng = rng
        self._current_event = None # нан это прибор свободен
        self._finish_time = 0.0 # окончание текущего анализа
        self._busy_time = 0.0 # сколько времени прибор проработал

    @property
    def id(self):
        return self._id

    @property
    def current_event(self):
        return self._current_event

    @property
    def finish_time(self):
        return self._finish_time

    @property
    def busy_time(self):
        return self._busy_time

    def is_free(self):
        return self._current_event is None

    def start(self, event):
        # ПЗ2 время анализа распределено равномерно
        # started_at у заявки диспетчер выставляет до вызова
        if not self.is_free():
            raise ValueError(f'Прибор {self._id} занят')
        self._current_event = event
        service = self._rng.uniform(self._service_min, self._service_max)
        self._finish_time = event.started_at + service
        return self._finish_time

    def finish(self):
        event = self._current_event
        event.mark_finished(self._finish_time)
        self._busy_time += event.service_time()
        self._current_event = None
        return event


class ModulePool:
    def __init__(self, modules):
        self._modules = modules

    def first_free(self):
        # Д2П1: всегда ищем с первого прибора, -1 если все заняты
        for module in self._modules:
            if module.is_free():
                return module.id
        return -1

    def get(self, module_id):
        return self._modules[module_id - 1]

    def size(self):
        return len(self._modules)

    def busy_times(self):
        return [module.busy_time for module in self._modules]
