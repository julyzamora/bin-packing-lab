import argparse
from .experiment import suite, benchmark
from .leaderboard import render
from .solvers import NAMES

p = argparse.ArgumentParser(description='Bin Packing Lab')
sub = p.add_subparsers(dest='command', required=True)
s = sub.add_parser('synthetic')
s.add_argument('path'); s.add_argument('--seed', type=int, default=17)
s.add_argument('--count', type=int, default=8)
b = sub.add_parser('benchmark')
b.add_argument('suite'); b.add_argument('--state', default='runs/research')
b.add_argument('--timeout', type=float, default=2)
b.add_argument('--solvers', nargs='+', choices=NAMES, default=list(NAMES))
l = sub.add_parser('leaderboard')
l.add_argument('--state', default='runs/research'); l.add_argument('--output', default='leaderboard')
a = p.parse_args()
if a.command == 'synthetic':
    print(f"Generated {len(suite(a.path, a.seed, a.count)['cases'])} development instances")
elif a.command == 'benchmark':
    print(benchmark(a.suite, a.state, a.solvers, a.timeout))
else:
    print(f"Rendered {len(render(a.state, a.output))} leaderboard entries")
