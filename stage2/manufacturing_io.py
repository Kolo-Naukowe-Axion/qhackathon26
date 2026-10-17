"""Read retained full/restricted QUBOs without running a reference solver."""
import json
from pathlib import Path
from .window_qubo import WindowQUBO
from .column_qubo import ColumnQUBO


def load(path):
    path=Path(path)
    case=path.parent if path.name=='full-domain'else path
    p=json.loads((case/'problem.json').read_text())
    r=json.loads((path/'qubo.json').read_text());m=r['metadata']
    args=(r['variables'],r['groups'],r['linear'],{(i,j):v for i,j,v in r['quadratic']},r['offset'],m['penalty'],m['feasible_objective_upper_bound'])
    if r['variables'][0].get('operation'):
        q=WindowQUBO(p,*args,{})
    else:
        columns=json.loads((case/'columns.json').read_text())
        q=ColumnQUBO(p,columns,r['groups'],r['variables'],r['linear'],args[3],r['offset'],m['penalty'],m['feasible_objective_upper_bound'],[])
    witness=json.loads((path/'witness.json').read_text())
    assert q.decode(witness['bits'])['valid']and q.energy(witness['bits'])==witness['energy']
    return q,r,witness
