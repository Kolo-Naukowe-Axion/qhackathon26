"""Public synthetic cases for direct classical validation and scaling.

These are new inputs, not replacements for the frozen method-owner release.
"""
import copy

from .domain import fixture, snapshot, validate_instance


def cases(include_scale=True):
    result = []

    def add(name, instance, scenario="S0", purpose=""):
        instance = copy.deepcopy(instance)
        instance["instance_id"] = name
        validate_instance(instance)
        result.append(dict(case_id=name, instance=instance, snapshot=snapshot(instance,scenario), purpose=purpose))

    for scenario in ("S0","S1","S2","S3"):
        add("core-"+scenario,fixture(),scenario,"Match frozen complete-program optimum")

    p = fixture()
    p["horizon_minutes"] = 160
    p["calendars"] = {r:[[0,160]] for r in p["calendars"]}
    p["urgent_groups"][0]["departure"] = 140
    p["previous_unstarted"] = []
    add("freshness-split",p,"S1","Two departures 50 minutes apart exceed the 40-minute freshness window")

    p = fixture()
    p["menus"]["B"]["yields"] = [2]
    p["menus"]["B"]["cooking"] = {"2":20}
    p["previous_unstarted"] = []
    add("unavoidable-surplus",p,purpose="One requested lot, only a two-lot yield: zero misses requires one waste lot")

    p = fixture()
    p["demand_groups"][1]["departure"] = 50
    p["previous_unstarted"] = []
    add("unreachable-handover",p,purpose="Earliest new B packing ends at 60, after its 50-minute departure")

    p = fixture()
    p["fixed_batches"] = [];p["previous_unstarted"] = [];p["urgent_groups"] = []
    p["demand_groups"] = [dict(id="B/priority-"+str(w),menu="B",lots=1,departure=60,revealed=0,priority=w)
                          for w in (1,5)]
    add("priority-bottleneck",p,purpose="One pack slot before departure: protect the five-weight customer")

    p = fixture()
    p["calendars"]["C2"] = [[0,40],[40,110]]
    p["calendars"]["W1"] = [[0,50],[50,110]]
    add("touching-calendars",p,purpose="Individual operations must fit one window, even when windows touch")

    p = fixture()
    p["workers"]["W4"] = ["prepare","pack"]
    p["calendars"]["W4"] = [[20,110]]
    p["calendars"]["W1"] = [[0,70]]
    add("alternative-qualified-worker",p,"S1","Additional eligible worker with distinct availability")

    if include_scale:
        for count in (4,8,12):
            p = fixture()
            p["horizon_minutes"] = 240
            p["menus"]["B"].update(yields=[1,2,4],cooking={"1":20,"2":20,"4":30},max_age=60)
            p["menus"]["C"] = dict(yields=[1,2,4],prepare=10,cooking={"1":10,"2":20,"4":30},
                                    cook_attendance=10,pack_per_lot=10,clean=10,max_age=60)
            p["equipment"]["prepare"].append("P2")
            p["workers"]["W4"] = ["prepare","pack"]
            p["workers"]["W5"] = ["cook","clean"]
            p["calendars"] = {r:[[0,240]] for r in sum(p["equipment"].values(),[])+list(p["workers"])}
            p["demand_groups"] = [p["demand_groups"][0]]+[
                dict(id=f"scale/{i}",menu="B" if i%2==0 else "C",lots=1+i%3,
                     departure=120+(i%6)*20,revealed=0,priority=1+(i%4==0)) for i in range(count)]
            p["urgent_groups"] = [];p["previous_unstarted"] = []
            add(f"scale-{count}-groups",p,purpose="Two residual menus, variable yields, alternative workers, packing pressure")
    return result
