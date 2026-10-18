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
