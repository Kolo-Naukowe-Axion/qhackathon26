"""Numerical synthetic instances. Every assumption is exported with the trace."""
from copy import deepcopy
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def build(orders=24, horizon=None, seed=0, profile="full"):
    b = json.loads((ROOT / "instances/stage2/metaltech_pressure.json").read_text())
    families = b["orders"]["families"]
    result = {k: deepcopy(b[k]) for k in ("machines", "workers", "recipes", "transport", "energy", "quality")}
    fine = profile != "coarse"
    scale=15 if fine else 1
    horizon=(5760 if fine else 384) if horizon is None else horizon
    result.update(schema="metaltech-stage2-instance.v1", name="MetalTech physical factory",
                  seed=seed, profile=profile, tick_minutes=1 if fine else 15, horizon_ticks=horizon,
                  day_ticks=96*scale,replan_ticks=4*scale)
    result["orders"] = [dict(id=f"P{i+1:02d}", family=families[i%3],
        release_tick=[0,8,16,24][i%4]*scale, due_tick=[160,184,208,232,256,280][i%6]*scale,
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
    result["certification_modes"]={"precision":{"T":["eco","standard"],"F":["eco","standard"],"QA":["precision"]}}
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
        component_defect_probability={"standard":.06,"precision":.02},
        risk_model="manufacturing_mode_history",repair_residual_probability=.02,
        wear_risk_coefficient=.01,
        manufacturing_defect_probabilities={"T":{"eco":.01,"standard":.025,"turbo":.08},
            "F":{"eco":.015,"standard":.03,"turbo":.10},"S":{"standard":.04,"careful":.015},
            "WASH":{"standard":.005},"HEAT":{"standard":.02},"ASSEMBLY":{"standard":.025,"careful":.01}})
    result["delivery"] = dict(id="D1",normal_tick=120,delayed_tick=156,contents={k:4 for k in ("housing","rotor","flange")})
    result["uncertainty_stages"]=deepcopy(b["uncertainty_stages"])
    result["attendance"]={p:{"kind":"start" if fine and p in ("T","F","WASH","HEAT") else "full",
        "ticks":5 if fine else 1} for p in result["modes"]}
    if fine:
        for recipe in result["recipes"].values():
            for step in recipe:step["base_ticks"]*=scale
        for m in result["setup_matrix"].values():
            for family in m:m[family]*=scale
        for w in result["workers"]:
            w["daily_shift"]=[x*scale for x in w["daily_shift"]]
            w["breaks"]=[[a*scale,z*scale] for a,z in w["breaks"]]
        for tool in result["tools"]:tool["life"]*=scale;tool["service_ticks"]*=scale
        result["maintenance"]["wear_limit"]*=scale;result["maintenance"]["duration"]*=scale
        for key in ("repair_ticks","replacement_lead_ticks"):result["quality"][key]*=scale
        result["energy"]["stationary_soc_unit_kwh"]/=scale
        for key in ("stationary_soc_capacity","stationary_soc_initial","stationary_soc_min","stationary_soc_terminal_min"):result["energy"][key]*=scale
        for key in ("normal_tick","delayed_tick"):result["delivery"][key]*=scale
        for stage in result["uncertainty_stages"]:
            stage["reveal_tick"]*=scale
            for outcome in stage["outcomes"]:
                for event in outcome["events"]:
                    for key in ("start","end","original_tick","new_tick","release_tick"):
                        if key in event:event[key]*=scale
    result["time_scale"]=scale
    result["transport"]["soc_unit_kwh"]=.005 if fine else .075
    result["lease_options"]=[dict(id="calibration-kit",cost=150,lead_ticks=32*scale,
        max_count=1,resource=dict(id="calibration_lease",kind="calibration",initial_location="TOOL_B",
            life=40*scale,service_ticks=4*scale))]
    result["investment_budget"]=250
    result["feature_status"]={name:"implemented; independently checkable in trace" for name in b["enabled_design_mechanisms"]}
    result["feature_status"].update(
        cost_carbon_budget="energy cost/carbon objectives and hard investment budget; operating/carbon caps not implemented",
        procurement_lead_times="scheduled stock delivery, delayed delivery, bounded replacement and tool rental; emergency buying not implemented",
        nonanticipative_recourse="causal revealed-state controller; robust start guards; empirical prefix audit, no general proof",
        rolling_wip="hourly dispatch policy updates; active reservations retained; initial burn-in snapshot not yet implemented",
        capacity_lease="one portable calibration kit with price, lead time, delivery location and budget; machine leasing not implemented")
    return result


def duration(instance,process,base,machine,mode):
    a,b=instance["modes"][process][mode]["duration_factor"]
    c,d=machine["duration_factor"]
    return (base*a*c+b*d-1)//(b*d)
