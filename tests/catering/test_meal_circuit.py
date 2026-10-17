import importlib.util
import unittest
import numpy as np

from catering.meal_blocks import meal_fixture,compile_meal_blocks,sector_data,sector_bits
from catering.meal_search import portfolio,warm_state,evolve
from catering.meal_circuit import circuit
from catering.domain import snapshot
from catering.options import enumerate_options


@unittest.skipUnless(importlib.util.find_spec("qiskit"),"Qiskit optional; run with .venv/bin/python")
class QiskitMealCircuitTests(unittest.TestCase):
    def test_sector_logical_native_and_routed_statevectors_agree(self):
        from qiskit import transpile
        from qiskit.quantum_info import Statevector
        from qiskit.transpiler import CouplingMap
        p=meal_fixture(1);s=snapshot(p,"S0");o=enumerate_options(p,s)
        b=compile_meal_blocks(p,s,portfolio(o,[],3,np.random.default_rng(1)))
        sec=sector_data(b);params=[(.27,.39,.41),(-.13,.51,-.23)]
        ground=sector_bits(b,sec,int(sec["energy"].argmin()))
        retained=[p["id"] for i,p in enumerate(b["options"]) if ground[i]]
        for initial_ids in ([],retained):
            expected=evolve(warm_state(b,sec,set(initial_ids)),sec,params,b["objective"]["weights"]["U"])
            qc=circuit(b,params,initial_ids);full=Statevector.from_instruction(qc).data
            masks=np.array([sum(x<<j for j,x in enumerate(sector_bits(b,sec,i))) for i in range(sec["states"])])
            np.testing.assert_allclose(full[masks],expected,atol=1e-10)
            self.assertAlmostEqual(float(sum(abs(full[masks])**2)),1)
            native=transpile(qc,basis_gates=["rz","sx","x","cx"],optimization_level=2,seed_transpiler=2026)
            np.testing.assert_allclose(Statevector.from_instruction(native).data,full,atol=1e-10)
            routed=transpile(qc,basis_gates=["rz","sx","x","cx"],coupling_map=CouplingMap.from_line(qc.num_qubits),
                             initial_layout=list(range(qc.num_qubits)),optimization_level=2,seed_transpiler=2026)
            permutation=routed.layout.final_index_layout(filter_ancillas=True)
            mapping=np.array([sum(((i>>j)&1)<<permutation[j] for j in range(qc.num_qubits)) for i in range(1<<qc.num_qubits)])
            np.testing.assert_allclose(Statevector.from_instruction(routed).data[mapping],full,atol=1e-10)


if __name__=="__main__":unittest.main()
