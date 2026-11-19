class Summary:
    def __init__(self, generated, processed, rejected, average_wait, average_service,
                 average_sojourn, wait_variance, service_variance,
                 module_utilization=(), per_camera=()):
        self._generated = generated
        self._processed = processed
        self._rejected = rejected
        self._average_wait = average_wait
        self._average_service = average_service
        self._average_sojourn = average_sojourn # среднее время пребывания
        self._wait_variance = wait_variance
        self._service_variance = service_variance
        self._module_utilization = tuple(module_utilization)
        self._per_camera = tuple(per_camera)

    @property
    def generated(self):
        return self._generated

    @property
    def processed(self):
        return self._processed

    @property
    def rejected(self):
        return self._rejected

    @property
    def rejection_probability(self):
        return self._rejected / self._generated if self._generated else 0.0

    @property
    def average_wait(self):
        return self._average_wait

    @property
    def average_service(self):
        return self._average_service

    @property
    def average_sojourn(self):
        return self._average_sojourn

    @property
    def wait_variance(self):
        return self._wait_variance

    @property
    def service_variance(self):
        return self._service_variance

    @property
    def module_utilization(self):
        return self._module_utilization

    @property
    def per_camera(self):
        return self._per_camera


class Statistics:
    """Счётчики по камерам, номера камер с единицы."""

    def __init__(self, cameras_count):
        n = cameras_count
        self._generated = [0] * n
        self._rejected = [0] * n
        self._completed = [0] * n
        self._wait_sum = [0.0] * n
        self._wait_sq_sum = [0.0] * n
        self._service_sum = [0.0] * n
        self._service_sq_sum = [0.0] * n
        self._sojourn_sum = [0.0] * n

    def record_generated(self, event):
        self._generated[event.camera_id - 1] += 1

    def record_rejected(self, event):
        self._rejected[event.camera_id - 1] += 1

    def record_completed(self, event):
        i = event.camera_id - 1
        wait = event.wait_time()
        service = event.service_time()
        self._completed[i] += 1
        self._wait_sum[i] += wait
        self._wait_sq_sum[i] += wait * wait
        self._service_sum[i] += service
        self._service_sq_sum[i] += service * service
        self._sojourn_sum[i] += event.sojourn_time()

    def summary(self, total_time, busy_times):
        count = len(self._generated)
        rows = [self._build([i]) for i in range(count)]
        utilization = [busy / total_time if total_time > 0 else 0.0 for busy in busy_times]
        return self._build(range(count), utilization, rows)

    def _build(self, indexes, utilization=(), per_camera=()):
        indexes = list(indexes)
        generated = sum(self._generated[i] for i in indexes)
        rejected = sum(self._rejected[i] for i in indexes)
        completed = sum(self._completed[i] for i in indexes)
        wait_sum = sum(self._wait_sum[i] for i in indexes)
        wait_sq = sum(self._wait_sq_sum[i] for i in indexes)
        service_sum = sum(self._service_sum[i] for i in indexes)
        service_sq = sum(self._service_sq_sum[i] for i in indexes)
        sojourn_sum = sum(self._sojourn_sum[i] for i in indexes)
        if completed:
            average_wait = wait_sum / completed
            average_service = service_sum / completed
            average_sojourn = sojourn_sum / completed
            # дисперсия = среднее квадратов минус квадрат среднего
            wait_variance = max(0.0, wait_sq / completed - average_wait ** 2)
            service_variance = max(0.0, service_sq / completed - average_service ** 2)
        else:
            average_wait = average_service = average_sojourn = 0.0
            wait_variance = service_variance = 0.0
        return Summary(generated, completed, rejected, average_wait, average_service,
                       average_sojourn, wait_variance, service_variance,
                       utilization, per_camera)
