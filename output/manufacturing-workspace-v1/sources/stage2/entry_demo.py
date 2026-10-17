"""Loopback-only entry demo with a fresh local quantum-simulation action.

Usage: .venv-stage2/bin/python -m stage2.entry_demo --port 4189
No credentials, remote adapters, network clients or external jobs are used.
"""
import argparse
from datetime import datetime, timezone
from functools import partial
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
from pathlib import Path
import time
from urllib.parse import urlparse
import uuid

from .assignment_qaoa import AssignmentSector, sample
from .entry_core import entry_cases
from .window_qubo import compile_qubo, solve_cp, digest
from .recipe_live import CASES as RECIPE_CASES, fresh_recipe

ROOT = Path(__file__).resolve().parents[1]


def fresh(case, seed):
    start = time.perf_counter()
    problem = entry_cases()[case]
    q = compile_qubo(problem, support_pruning=True)
    sector = AssignmentSector.build(q)
    row = sample(sector,seed=seed,layers=2,alpha=.25,shots=8192,evaluations=128)
    reference = solve_cp(problem,seconds=10,workers=1)
    stamp = datetime.now(timezone.utc)
    name = stamp.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    directory = ROOT/'output'/'stage2-entry-live'/name
    directory.mkdir(parents=True,exist_ok=False)
    sources = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
               ['stage2/entry_demo.py','stage2/entry_core.py','stage2/assignment_qaoa.py',
                'stage2/window_qubo.py','stage2/window_reduction.py']}
    result = dict(schema='qfactoria-fresh-entry-run.v1', case=case,seed=seed,
                  created_utc=stamp.isoformat(), fresh=True, result=row, reference=reference,
                  problem_sha256=digest(problem), source_hashes=sources,
                  local_artifact=str(directory.relative_to(ROOT)),
                  physical_qpu_calls=0,veloxq_calls=0,
                  elapsed_seconds=time.perf_counter()-start)
    (directory/'problem.json').write_text(json.dumps(problem,indent=2)+'\n')
    (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    (directory/'circuit.qasm').write_text(row['qasm'])
    (directory/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                                    for p in directory.iterdir()},indent=2)+'\n')
    return result


class Handler(SimpleHTTPRequestHandler):
    def local(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')

    def respond(self, code, value):
        data=json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.local():
            return self.respond(403,dict(error='Loopback Host required'))
        if urlparse(self.path).path == '/api/status':
            return self.respond(200,dict(enabled=True,recipe_enabled=True,remote_calls=0))
        return super().do_GET()

    def do_POST(self):
        if not self.local():
            return self.respond(403,dict(error='Loopback Host required'))
        if self.path not in ('/api/solve','/api/solve-recipe'):
            return self.respond(404,dict(error='Unknown action'))
        allowed=[f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']
        if self.headers.get('Origin') not in allowed or self.headers.get('Content-Type') != 'application/json':
            return self.respond(403,dict(error='Same-origin JSON action required'))
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=1024:
                raise ValueError('Bounded JSON request required')
            value=json.loads(self.rfile.read(length))
            case,seed=value['case'],value['seed']
            choices=RECIPE_CASES if self.path=='/api/solve-recipe' else entry_cases()
            if case not in choices or type(seed)is not int or not 0<=seed<=1_000_000:
                raise ValueError('Unknown case or seed outside 0..1000000')
            cap=value.get('cap',3)
            if self.path=='/api/solve-recipe' and (type(cap)is not int or cap not in (2,3,4)):
                raise ValueError('Component cap outside2/3/4')
        except (ValueError,KeyError,TypeError):
            return self.respond(400,dict(error='Choose a listed case and integer seed 0..1000000'))
        try:
            result=fresh_recipe(case,seed,cap) if self.path=='/api/solve-recipe' else fresh(case,seed)
        except Exception as exc:
            return self.respond(500,dict(error=type(exc).__name__))
        return self.respond(200,result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=4189)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT/'presentation')))
    print(f'Local fresh-run demo: http://127.0.0.1:{args.port}/entry/',flush=True)
    server.serve_forever()
