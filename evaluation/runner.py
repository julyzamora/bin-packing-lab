"""Container entrypoint; only assignments cross the trust boundary."""
import importlib.util
import json
import sys
spec = importlib.util.spec_from_file_location('candidate', '/candidate/solver.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
request = json.load(sys.stdin)
print(json.dumps({'assignment': module.solve(request['instance'], request['seed'])}))
