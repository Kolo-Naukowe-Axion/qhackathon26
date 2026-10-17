"""Public stable loaders, normalized samples and common budgets."""
import json
from pathlib import Path
from .qubo import validate_bundle


def load_bundle(path):
    return validate_bundle(json.loads(Path(path).read_text()))


def save_json(path, data):
    Path(path).write_text(json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n")


def method_result(bundle, method, samples, *, timings=None, work=None, reference=None):
    import platform
    return dict(schema_version="catering-method-result.v1", method_id=method, method_version=1,
                case_id=bundle["case_id"], bundle_sha256=bundle["bundle_sha256"],
                representation_id=bundle["representation_id"], execution_kind="classical",
                status="completed", samples=samples, timings=timings or {}, work=work or {},
                configuration={}, environment=dict(python=platform.python_version(), processor=platform.machine()),
                raw_artifacts=[], reference=reference, physical_qpu_calls=0, veloxq_calls=0)
