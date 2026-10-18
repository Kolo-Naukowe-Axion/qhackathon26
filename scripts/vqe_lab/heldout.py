import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
pre = json.load(open("heldout_predeclaration.json"))
cfgs = [(pre["primary"]["name"], pre["primary"]["cfg"])] + [(c["name"], c["cfg"]) for c in pre["controls"]]
J = [(n, case, cfg, s) for case in ("S3", "S2") for n, cfg in cfgs for s in pre["seeds"]]
df = lab.run_grid(J, "heldout_runs.csv", procs=9)
print("done", len(df))
