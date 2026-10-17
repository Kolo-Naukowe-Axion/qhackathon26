"""Native CP references for offline manufacturing packet preparation."""
import argparse
import json
from pathlib import Path
from .entry_core import entry_cases,recovery_cell
from .window_qubo import solve_cp,digest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    problems=entry_cases()
    problems.update({f'scale-{n}-pumps':recovery_cell(180+120*(n-1),pumps=n)for n in [2,4,8]})
    for name,problem in problems.items():
        directory=args.output/name
        directory.mkdir()
        result=dict(problem_sha256=digest(problem),reference=solve_cp(problem,seconds=10,workers=1))
        (directory/'reference.json').write_text(json.dumps(result,indent=2)+'\n')
        print(name,result['reference']['status'],result['reference'].get('objective'),flush=True)
