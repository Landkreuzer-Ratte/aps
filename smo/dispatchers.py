from models import Event, EventType


class AdmissionResult:
    def __init__(self, slot, evicted):
        self.slot = slot
        self.evicted = evicted


class Assignment:
    def __init__(self, event, module_id, slot):
        self.event = event
        self.module_id = module_id
        self.slot = slot


class AdmissionDispatcher:
    """Диспетчер постановки. С приборами не работает, только с буфером."""

    def __init__(self, buffer, statistics):
        self._buffer = buffer
        self._statistics = statistics

    def accept(self, event):
        evicted = None
        slot = self._buffer.first_free_slot()
        if slot == -1:
            # буфер полон, значит все приборы заняты: выбиваем самую старую
            slot = self._buffer.oldest_slot()
            evicted = self._buffer.remove(slot)
            evicted.mark_rejected(event.arrived_at)
            self._statistics.record_rejected(evicted)
        event.mark_queued(event.arrived_at)
        self._buffer.put(slot, event)
        return AdmissionResult(slot, evicted)


class SelectionDispatcher:
    """Диспетчер выбора. Запускается, когда заявка попала в буфер или освободился прибор."""

    def __init__(self, buffer, module_pool, calendar):
        self._buffer = buffer
        self._module_pool = module_pool
        self._calendar = calendar

    def on_event_queued(self):
        return self._assign_while_possible()

    def on_module_freed(self):
        return self._assign_while_possible()

    def _assign_while_possible(self):
        assignments = []
        while not self._buffer.is_empty():
            module_id = self._module_pool.first_free()
            if module_id == -1:
                break
            slot = self._buffer.newest_slot()
            event = self._buffer.remove(slot)
            event.mark_started(self._calendar.now)
            finish_time = self._module_pool.get(module_id).start(event)
            self._calendar.schedule(Event(finish_time, EventType.ANALYSIS_COMPLETION,
                                          camera_id=event.camera_id, module_id=module_id))
            assignments.append(Assignment(event, module_id, slot))
        return assignments
