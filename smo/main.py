import argparse

from simulation import Simulation, SimulationConfig

def read_args():
    defaults = SimulationConfig()
    parser = argparse.ArgumentParser(
        description='Модель СМО: охрана периметра с тепловизионными камерами (вариант 25)')
    parser.add_argument('mode', choices=['auto', 'step'],
                        help='auto - сводная таблица, step - пошаговый режим')
    parser.add_argument('--cameras', type=int, default=defaults.cameras, help='число камер')
    parser.add_argument('--rate', type=float, default=defaults.rate,
                        help='событий в секунду от одной камеры')
    parser.add_argument('--modules', type=int, default=defaults.modules, help='число приборов')
    parser.add_argument('--buffer', type=int, default=defaults.buffer_capacity,
                        help='число ячеек буфера')
    parser.add_argument('--service-min', type=float, default=defaults.service_min,
                        help='минимальное время анализа, сек')
    parser.add_argument('--service-max', type=float, default=defaults.service_max,
                        help='максимальное время анализа, сек')
    parser.add_argument('--requests', type=int, default=defaults.request_limit,
                        help='сколько заявок сформировать')
    parser.add_argument('--seed', type=int, default=None, help='зерно генератора случайных чисел')
    return parser.parse_args()


def run_step_mode(simulation):
    print('Пошаговый режим: Enter - следующий шаг, a - до конца, q - выход')
    to_end = False
    while simulation.run_step():
        if to_end:
            continue
        try:
            command = input('> ').strip().lower()
        except EOFError:
            command = 'a'
        if command == 'q':
            print('Остановлено.')
            return
        if command == 'a':
            to_end = True
    simulation.finish()


def main():
    args = read_args()
    config = SimulationConfig(cameras=args.cameras, rate=args.rate, modules=args.modules,
                              buffer_capacity=args.buffer, service_min=args.service_min,
                              service_max=args.service_max, request_limit=args.requests,
                              seed=args.seed)
    if args.mode == 'auto':
        Simulation(config).run_auto()
    else:
        run_step_mode(Simulation(config, step_mode=True))


if __name__ == '__main__':
    main()
