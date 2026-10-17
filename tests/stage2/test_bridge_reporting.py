import importlib.util
from pathlib import Path
import unittest


path=Path(__file__).resolve().parents[2]/'presentation/manufacturing/build-merit-data.py'
spec=importlib.util.spec_from_file_location('merit_exporter_for_test',path)
exporter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class BridgeReportingTests(unittest.TestCase):
    def test_matching_objective_with_invalid_encoding_is_not_optimal(self):
        def record(valid,objective,energy=None):
            return dict(method='uniform_onehot',decoded=dict(valid=valid,objective=objective),
                        energy=objective if energy is None else energy,exact_hit_probability=.1,wall_seconds=.01)
        row=dict(reference=dict(objective=855),runs=[record(False,855),record(True,855),record(True,945),record(True,855,885)])
        summary=exporter.method_summary(row,'uniform_onehot')
        self.assertEqual(summary['runs'],4)
        self.assertEqual(summary['valid'],3)
        self.assertEqual(summary['pool_optimal'],1)


if __name__=='__main__':unittest.main()
