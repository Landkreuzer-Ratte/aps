class Buffer:
    def __init__(self, capacity):
        self._slots = [None] * capacity

    @property
    def capacity(self):
        return len(self._slots)

    def first_free_slot(self):
        # Д1ОЗ3 первая свободная ячейка с начала, -1 если мест нет
        for index, event in enumerate(self._slots):
            if event is None:
                return index
        return -1

    def oldest_slot(self):
        #Д1ОО3 самая старая заявка (по времени поступления)
        return self._find_slot(newest=False)

    def newest_slot(self):
        # Д2Б2 самая поздняя заявка, LIFO
        return self._find_slot(newest=True)

    def put(self, slot, event):
        if self._slots[slot] is not None:
            raise ValueError(f'Ячейка {slot + 1} уже занята')
        self._slots[slot] = event

    def remove(self, slot):
        event = self._slots[slot]
        if event is None:
            raise ValueError(f'Ячейка {slot + 1} пуста')
        self._slots[slot] = None
        return event


    def is_empty(self):
        return all(event is None for event in self._slots)

    def snapshot(self):
        return tuple(self._slots)

    def _find_slot(self, newest):
        # сдвига нет, поэтому порядок в буфере смотрим по времени постановки, а не по номеру ячейки
        busy = [(event.arrived_at, index)
                for index, event in enumerate(self._slots) if event is not None]
        if not busy:
            return -1
        if newest:
            return max(busy)[1] # 10:01:02 < 12:15:59
        return min(busy)[1]
