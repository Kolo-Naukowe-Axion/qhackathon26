import sys,json
sys.path.insert(0,'.')
import catering.meal_reference as mr
from catering.contracts import load_bundle
from catering.decode import decode
w=int(sys.argv[1]);secs=float(sys.argv[2])
b=load_bundle(f'output/catering-velox-scale-v3/scale-{w}-qubo.json')
from ortools.sat.python import cp_model
orig=cp_model.CpSolver
class S(orig):
    def __init__(s):
        super().__init__()
    def Solve(s,m,*a):
        s.parameters.num_search_workers=4
        return super().Solve(m,*a)
cp_model.CpSolver=S
r=mr.solve_bundle(b,seconds=secs)
m=r['check']['metrics'] if r['check'] else None
print(w,r['reference']['status'],m,r['reference']['bound'],r['reference']['objective'])
json.dump(r,open(sys.argv[3],'w'))
