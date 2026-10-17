"""Nominal Bonferroni intervals for the two predeclared quantum mean contrasts.

Bootstrap uncertainty is empirical and conditional on the observed factory
tapes/actors; nominal family coverage is approximate, not a finite-sample proof.
"""
from collections import defaultdict
import math
import random

from .statistics import clustered_rows,weighted_mean


def mean_interval(left,right,protocol,metric,*,bootstrap=2000,seed=60819,family_size=2):
    if type(bootstrap) is not int or bootstrap<1000:raise ValueError('At least1000 replicates required for tail intervals')
    if type(family_size) is not int or family_size<1:raise ValueError('Positive integer family size required')
    a=clustered_rows(left,protocol,metric);b=clustered_rows(right,protocol,metric)
    if [(r['seed'],r['weight']) for r in a]!=[(r['seed'],r['weight']) for r in b]:raise ValueError('Unpaired factory tapes')
    differences=[y['value']-x['value'] for x,y in zip(a,b)];weights=[r['weight'] for r in a]
    groups=defaultdict(list)
    for index,row in enumerate(a):groups[row['leaf']].append(index)
    rng=random.Random(seed);values=[]
    for _ in range(bootstrap):
        chosen=[rng.choice(indices) for indices in groups.values() for _ in indices]
        values.append(weighted_mean([differences[i] for i in chosen],[weights[i] for i in chosen]))
    values.sort();tail=.05/(2*family_size)
    low=math.floor(tail*(len(values)-1));high=math.ceil((1-tail)*(len(values)-1))
    return dict(mean_difference=weighted_mean(differences,weights),
        direction='Right minus left; negative favors right for a loss',
        percentile_interval=[values[low],values[high]],individual_nominal_coverage=1-.05/family_size,
        family_size=family_size,nominal_family_error_rate=.05,bootstrap_replicates=bootstrap,bootstrap_seed=seed,
        environment_tapes=len(a),actor_replicas_left=sum(r['actor_replicas'] for r in a),
        actor_replicas_right=sum(r['actor_replicas'] for r in b),
        scope='Whole paired environment clusters resampled within leaves; actors remain nested. Nominal Bonferroni adjustment for the predeclared family only; bootstrap coverage is approximate.')
