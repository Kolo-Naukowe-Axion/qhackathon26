"""Numerical synthetic instances. Every assumption is exported with the trace."""
from copy import deepcopy
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def build(orders=24, horizon=384, seed=0, profile="full"):
    b = json.loads((ROOT / "instances/stage2/metaltech_pressure.json").read_text())
    families = b["orders"]["families"]
    result = {k: deepcopy(b[k]) for k in ("machines", "workers", "recipes", "transport", "energy", "quality")}
    result.update(schema="metaltech-stage2-instance.v1", name="MetalTech physical factory",
                  seed=seed, profile=profile, tick_minutes=15, horizon_ticks=horizon)
    result["orders"] = [dict(id=f"P{i+1:02d}", family=families[i%3],
        release_tick=[0,8,16,24][i%4], due_tick=[160,184,208,232,256,280][i%6],
        precision_required=(i+1)%4==0, urgent=False) for i in range(orders)]
    result["units"] = [dict(id=f'{o["id"]}/{kind}/1', order_id=o["id"], recipe=kind,
        family=o["family"], release_tick=o["release_tick"], initial_location="RAW_A")
        for o in result["orders"] for kind in ("housing","rotor","flange")]
    powers = {"T":9,"F":12,"S":10,"WASH":4,"HEAT":16,"QA":3,"ASSEMBLY":4}
    result["modes"] = {}
    for p, modes in b["mode_duration_factors"].items():
        result["modes"][p] = {name:dict(duration_factor=factor,
            power_kw=powers[p]*({"eco":.65,"turbo":1.5,"careful":.8,"precision":1.2}.get(name,1)),
            wear={"turbo":2,"eco":.6}.get(name,1),
            defect_probability={"turbo":.10,"eco":.025,"careful":.01,"precision":.01}.get(name,.04))
            for name,factor in modes.items()}
    result["setup_matrix"] = {a:{c:(0 if a==c else 2+(a=="alloy_C" or c=="alloy_C")) for c in families} for a in families}
    result["transport"].update(load_ticks=1,unload_ticks=1,charge_rate=12,charge_power_kw=4,
        charger_capacity=1, offlane_agv_capacity=4, charge_saturates=True)
    result["agvs"] = [dict(id=f"AGV{i+1}",initial_location="RAW_A",initial_soc=120,capacity=160) for i in range(4)]
    result["tools"] = [dict(id=f"{kind}{i+1}",kind=kind,initial_location="TOOL_A" if kind=="mill" else "TOOL_B",
        life=40,service_ticks=4) for kind,n in (("mill",2),("weld",2),("calibration",1)) for i in range(n)]
    result["process_tools"] = {"F":"mill","S":"weld","QA":"calibration"}
    result["process_skills"] = {"T":"machining","F":"machining","S":"welding","WASH":"setup","HEAT":"setup","QA":"qa","ASSEMBLY":"assembly"}
    result["maintenance"] = dict(wear_limit=70,duration=5,skill="maintenance",power_kw=2,reset_family=False)
    result["worker_travel_ticks"] = 2
    # One hour of breaks in each eight-hour shift; no work may span a break.
    for w in result["workers"]:
        a,z=w["daily_shift"]; w["breaks"]=[[a+14,a+16],[a+26,a+28]]
        w["initial_hall"]="A" if "machining" in w["skills"] or "maintenance" in w["skills"] else "B"
    edges=[]
    for m in result["machines"]:
        edges.append(dict(a=m["id"],b=f'HUB_{m["hall"]}',ticks=1))
    for node,hall in (("RAW_A","A"),("TOOL_A","A"),("TOOL_B","B"),("SHIP_B","B"),("SCRAP_B","B"),("CHARGE_A","A"),("CHARGE_B","B")):
        edges.append(dict(a=node,b=f"HUB_{hall}",ticks=1))
    edges.append(dict(a="HUB_A",b="HUB_B",ticks=4))
    result["graph_edges"]=edges
    result["energy"].update(tariff_low=.12,tariff_peak=.34,carbon_low=.25,carbon_peak=.65,
        solar_peak_kw=16, no_export=True)
    result["raw_stock_units"]={kind:30 for kind in ("housing","rotor","flange")}
    result["quality"].update(repair_ticks=3,repair_power_kw=8,repair_skill="machining",
        replacement_lead_ticks=12, final_defect_probability=.025,
        component_defect_probability={"standard":.06,"precision":.02})
    result["delivery"] = dict(id="D1",normal_tick=120,delayed_tick=156,contents={k:4 for k in ("housing","rotor","flange")})
    result["uncertainty_stages"]=deepcopy(b["uncertainty_stages"])
    result["feature_status"]={name:"planned" for name in b["enabled_design_mechanisms"]}
    return result


def duration(instance,process,base,machine,mode):
    a,b=instance["modes"][process][mode]["duration_factor"]
    c,d=machine["duration_factor"]
    return (base*a*c+b*d-1)//(b*d)
