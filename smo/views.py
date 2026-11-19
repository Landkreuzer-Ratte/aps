from models import EventType


def format_table(headers, rows):
    text_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in text_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    line = '+-' + '-+-'.join('-' * width for width in widths) + '-+'

    def make_row(cells):
        return '| ' + ' | '.join(cell.ljust(width) for cell, width in zip(cells, widths)) + ' |'

    result = [line, make_row(headers), line]
    result.extend(make_row(row) for row in text_rows)
    result.append(line)
    return '\n'.join(result)


def percent(value):
    return f'{value * 100:.2f}%'


class StepView:
    """ОД1 состояние системы после каждого шага"""

    def __init__(self, calendar, buffer, module_pool, statistics):
        self._calendar = calendar
        self._buffer = buffer
        self._module_pool = module_pool
        self._statistics = statistics
        self._step = 0

    def render(self, actions):
        self._step += 1
        now = self._calendar.now
        summary = self._statistics.summary(now, self._module_pool.busy_times())

        print()
        print(f'=== Шаг {self._step} | модельное время t = {now:.4f} ===')
        print('События шага:')
        for action in actions:
            print(f'  - {action}')

        print('\nКалендарь событий (ближайшее сверху):')
        calendar_rows = []
        upcoming = self._calendar.upcoming()
        for number, event in enumerate(upcoming, start=1):
            if event.type is EventType.DETECTION_ARRIVAL:
                where = f'камера {event.camera_id}'
            else:
                where = f'прибор {event.module_id}'
            calendar_rows.append((number, f'{event.time:.4f}', event.type.value, where))
        print(format_table(('№', 'Время', 'Событие', 'Источник/прибор'), calendar_rows))

        print('\nИсточники:')
        source_rows = []
        for number, row in enumerate(summary.per_camera, start=1):
            next_time = '-'
            for event in upcoming:
                if event.type is EventType.DETECTION_ARRIVAL and event.camera_id == number:
                    next_time = f'{event.time:.4f}'
                    break
            source_rows.append((number, row.generated, row.rejected, next_time))
        print(format_table(('Камера', 'Сформировано', 'Отказов', 'Следующая заявка'), source_rows))

        print('\nБуфер:')
        buffer_rows = []
        for slot, event in enumerate(self._buffer.snapshot(), start=1):
            if event is None:
                buffer_rows.append((slot, 'свободна', '', ''))
            else:
                buffer_rows.append((slot, f'заявка №{event.id}', f'камера {event.camera_id}',
                                    f'{event.arrived_at:.4f}'))
        print(format_table(('Ячейка', 'Заявка', 'Источник', 'Поступила'), buffer_rows))

        print('\nПриборы:')
        module_rows = []
        for module_id in range(1, self._module_pool.size() + 1):
            module = self._module_pool.get(module_id)
            if module.is_free():
                module_rows.append((module_id, 'свободен', '', ''))
            else:
                module_rows.append((module_id, 'занят', f'заявка №{module.current_event.id}',
                                    f'{module.finish_time:.4f}'))
        print(format_table(('Прибор', 'Состояние', 'Заявка', 'Конец анализа'), module_rows))

        print(f'\nСтатистика: сформировано {summary.generated}, обработано {summary.processed}, '
              f'отказов {summary.rejected} ({percent(summary.rejection_probability)})')


class SummaryView:
    """ОР1: сводная таблица результатов."""

    def render(self, summary):
        print('\n=== Результаты моделирования ===')
        overall = [
            ('Сформировано заявок', summary.generated),
            ('Обработано заявок', summary.processed),
            ('Отказов', summary.rejected),
            ('Вероятность отказа', percent(summary.rejection_probability)),
            ('Среднее время ожидания', f'{summary.average_wait:.5f}'),
            ('Среднее время обслуживания', f'{summary.average_service:.5f}'),
            ('Среднее время пребывания', f'{summary.average_sojourn:.5f}'),
            ('Дисперсия времени ожидания', f'{summary.wait_variance:.7f}'),
            ('Дисперсия времени обслуживания', f'{summary.service_variance:.7f}'),
        ]
        print(format_table(('Показатель', 'Значение'), overall))

        print('\nПо источникам:')
        camera_rows = []
        for number, row in enumerate(summary.per_camera, start=1):
            camera_rows.append((number, row.generated, row.processed, row.rejected,
                                percent(row.rejection_probability),
                                f'{row.average_wait:.5f}', f'{row.average_service:.5f}',
                                f'{row.average_sojourn:.5f}'))
        print(format_table(('Камера', 'Сформ.', 'Обраб.', 'Отказ', 'P отказа',
                            'Ожидание', 'Обслуж.', 'Пребыв.'), camera_rows))

        print('\nЗагрузка приборов:')
        module_rows = [(number, percent(load))
                       for number, load in enumerate(summary.module_utilization, start=1)]
        print(format_table(('Прибор', 'Загрузка'), module_rows))
