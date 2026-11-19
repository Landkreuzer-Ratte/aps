from enum import Enum


class SignatureType(Enum):
    HUMAN = 'человек'
    VEHICLE = 'автомобиль'
    ANIMAL = 'животное'


class DayNight(Enum):
    DAY = 'день'
    NIGHT = 'ночь'


class EventType(Enum):
    DETECTION_ARRIVAL = 'поступление заявки'
    ANALYSIS_COMPLETION = 'окончание анализа'


class DetectionEvent:
    """
    Заявка - событие обнаружения от камеры.
    У неёё в идеале должен быть датчик движения (что-то типа сонара или другой датчик, главное физически засекает
    движение в некоторой области перед камерой), но это не обязательно, хватит тепловизора и самой камеры. 
    
    Камера 'умная', то есть за небольшой отрезок времени (от нескольких мс до 0.5-1 с, в зависимости от железа в камере)
    она должна проанализировать  изображенеи с самой камеры и тепловизора + датчик если он есть,
    сопоставить это всё(таким образом меньше ложных срабатываний, ведь уже 2-3 источника данных) и решить, стоит ли 
    отправлять данные на дальнейший анализ и степень уверенности в достоверности срабатывания(допустим, сравнивая 
    изображение и тепловую сигнатуру с загруженными в камеру часто встречающимися образами человека, машины и животных)
    и сохранять ли эту запись. При этом камера не находится 24/7 в режиме макс нагрузки, так как обычно изображение 
    статично и полноценный анализ (т.е. загрузка процессора в 80-100%) происходит только когда статичная картинка как-то
    меняется. 
    
    У камеры так же есть 'периметр' - при монтаже камеры на стену или ещё куда-то ей устанавливают её 
    координаты(относительно чего-то либо же абсолютные) и относительно этих координат выставляются координаты
    периметра и так же относительно этих коо-нат определяется положение объекта. Имея эти данные она определяет
    был ли пересечён периметр. Всё это происходит при анализе изображения.
    """

    def __init__(self, event_id, camera_id, target_x, target_y, signature,
                 confidence, mode, perimeter_crossed, arrived_at):
        self._id = event_id #номер заявки
        self._camera_id = camera_id # id камеры 1 2 3...
        self._target_x = target_x # координаты объекта
        self._target_y = target_y
        self._signature = signature # человек живтное машина
        self._confidence = confidence # уверенность
        self._mode = mode #день ночь
        self._perimeter_crossed = perimeter_crossed
        self._arrived_at = arrived_at # когда поступило в систему
        self._queued_at = None # когда поставили в буфер
        self._started_at = None # когда прибор начал анализ
        self._finished_at = None # когда кончился анализ
        self._rejected_at = None # когда заявка получила отказ

    @property
    def id(self):
        return self._id

    @property
    def camera_id(self):
        return self._camera_id

    @property
    def signature(self):
        return self._signature

    @property
    def confidence(self):
        return self._confidence

    @property
    def mode(self):
        return self._mode

    @property
    def perimeter_crossed(self):
        return self._perimeter_crossed

    @property
    def target(self):
        return (self._target_x, self._target_y)

    @property
    def arrived_at(self):
        return self._arrived_at

    @property
    def queued_at(self):
        return self._queued_at

    @property
    def started_at(self):
        return self._started_at

    @property
    def finished_at(self):
        return self._finished_at

    @property
    def rejected_at(self):
        return self._rejected_at

    def mark_queued(self, time):
        self._queued_at = time

    def mark_started(self, time):
        self._started_at = time

    def mark_finished(self, time):
        self._finished_at = time

    def mark_rejected(self, time):
        self._rejected_at = time

    def wait_time(self):
        return self._started_at - self._queued_at

    def service_time(self):
        return self._finished_at - self._started_at

    def sojourn_time(self):
        return self._finished_at - self._arrived_at


class Event:
    """Запись в календаре событий"""

    def __init__(self, time, event_type, camera_id=None, module_id=None):
        self._time = time
        self._type = event_type
        self._camera_id = camera_id
        self._module_id = module_id

    @property
    def time(self):
        return self._time

    @property
    def type(self):
        return self._type

    @property
    def camera_id(self):
        return self._camera_id

    @property
    def module_id(self):
        return self._module_id
