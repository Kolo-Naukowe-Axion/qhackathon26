"""No solving: each investment variant changes exactly its declared resource."""
import copy

from catering.domain import snapshot
from catering.investment import VARIANTS
from catering.meal_blocks import meal_fixture


def test_variants_change_only_their_resource():
    base = meal_fixture(12)
    for name, _, change, scenario in VARIANTS:
        instance = copy.deepcopy(base)
        if change:
            change(instance)
        changed = {k for k in instance if instance[k] != base[k]}
        assert changed <= {'equipment', 'calendars', 'workers'}, name
        if name == 'second-pack':
            continue
        state = snapshot(instance, scenario)
        assert state['scenario_id'] == scenario
        assert bool(state['outages']) == (scenario == 'S3'), name


def test_investment_page_data_matches_retained_results():
    import importlib.util
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location('export_investment', root/'scripts/export-catering-investment.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = module.export()
    assert (root/'presentation/catering/investment/data.json').read_text() == module.render(data), \
        'Run scripts/export-catering-investment.py'
    rows = {v['id']: v for v in data['variants']}
    assert len(rows) == len(VARIANTS) and rows['second-pack']['status'] == 'unsupported'
    assert rows['baseline']['tuple'] == [5, 1, 10, 10] and rows['third-cooker']['tuple'][0] == 5
    assert data['decision']['fewest_skills_sufficient'] == 'worker-pack'
    assert data['decision']['equally_few_skills'] == ['worker-prepare', 'worker-pack']
    assert not data['decision']['equipment_improved_service_in_runs']
