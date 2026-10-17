# Stage 2 trace v1

Root object: `schema: metaltech-stage2-trace.v1`, `run_id`, `tick_minutes`,
`horizon_ticks`, `provenance`, `instance` (complete public numerical tables),
`resources` (machines/agvs/workers/tools), `operations`, `moves`, `events`,
`energy`, `validation`, `metrics`. All intervals are half open integer ticks.
`tick_minutes` defines the unit: the full profile uses one minute and 5,760
ticks; the archived coarse profile uses 15 minutes. `instance.day_ticks`
defines calendars independently of resolution.
At a boundary: previous activity completions/dropoffs; revealed events/releases;
new decisions; energy for the ensuing interval. No future outcome is passed to
the policy. Audit tapes are post-run evidence, never controller input.

`operations`: records `{id, unit_ids, unit_id, order_id, process, machine_id,
start, end, mode, worker_ids, tool_ids, parent_unit_ids, setup_ticks,
processing_ticks, power_kw, family, kind}`. `kind` is process, maintenance or
tool_service. Start includes setup; process duration follows setup. Tools cover
the whole interval. `worker_intervals` lists `{worker_id,start,end,role,skills}`.
Robotic T/F/WASH/HEAT attendance covers five minutes of tending after setup;
S/QA/ASSEMBLY need full processing attendance. A qualified setup worker covers
every family-change setup, either the process worker or a separate crew member.
Machine output remains occupied after completion until every batch member's
pickup. Input buffers are distinct from machine output. For assembly,
`parent_unit_ids` are consumed at start. The pump identity enters processing at
that boundary; its assembled output becomes available at completion.
All other process inputs are `unit_ids`. No operation overlaps any reservation
on its machine. A completed QA marks a component accepted or generates a bounded
repair/scrap decision via an event.

`moves`: `{id, unit_id, entity_type:'part'|'tool'|null, agv_id, start,
pickup_tick, drop_tick, end, from, to, legs:[{from,to,start,end,loaded}],
soc_before,soc_after,kind:'transport'|'charge'}`. Empty repositioning precedes
pickup; one tick load, then loaded legs, then one tick unload. For charge,
unit_id=null and charge starts after empty repositioning. Destination input
space reserved at `start`, released at `drop_tick` to physical occupancy. A part
leaves its source at `pickup_tick`. Every leg uses an undirected single lane;
the full inter-hall bridge is one lane of four ticks. Off-lane parking/holding
capacity is four AGVs at hubs/stations. Travel consumes 1 empty/2 loaded SOC
per tick; load/unload has no traction draw. Charger charge rate is explicit.

`events`: `{tick,type,resource_id?,unit_id?,description,...}`. Types include
release, process_complete, qa_result, consume, ship, outage, grid_derating,
repair, scrap, replacement, procurement, maintenance_complete.

`energy`: `{tick,load_kw,grid_kw,cap_kw,solar_kw,curtailed_kw,soc_before,soc,
battery_action,tariff,carbon_intensity}`. Convert integer stationary SOC using
`instance.energy.stationary_soc_unit_kwh`: the full minute profile uses 1/60kWh
per SOC unit (2400 units =40kWh); the archived coarse profile uses .25kWh.
Machine load from active operation record `power_kw` plus base load and AGV
charging. Charge/discharge uses the blueprint's explicit lossy action table.

`instance` supplies `orders`, `units`, `machines`, `workers`, `tools`, `agvs`,
`graph_edges`, `recipes`, `modes`, `setup_matrix`, `transport`, `energy`,
`quality`, `feature_status`; generation seed and realized audit events appear
in `audit`. The checker must label implemented checks and unsupported features
explicitly. A partial horizon is a valid partial trace, not a feasible complete
solution. Fulfillment and terminal requirements are reported separately.

The actual quality draw key is `quality:{unit_id}:{attempt}`; process-operation
IDs are diagnostic references, not random-stream keys. Replacement unit IDs
extend the lineage. Numerical seeds and post-inspection uniforms in saved traces
are audit evidence, not inputs to the observation-only learned controller.
