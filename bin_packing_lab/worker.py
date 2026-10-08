"""One trusted baseline invocation; a subprocess is NOT a security sandbox."""
import json
import sys
import time
from .solvers import solve

request = json.load(sys.stdin)
start = time.perf_counter_ns()
assignment = solve(request['instance'], request['solver'], request['seed'])
json.dump({'assignment': assignment, 'algorithm_ns': time.perf_counter_ns()-start}, sys.stdout)
