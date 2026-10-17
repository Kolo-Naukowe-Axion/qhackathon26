# Our Stage 2 factory: the problem, every system, and the encoding

This is a written explanation of the project as it exists on 17 October 2026. Read it in order: first the factory, then the mathematical representation. Optimization remains paused. Nothing in this document launches a solver.

The main model is a synthetic pump factory that we designed. Its numerical assumptions are ours, not an industrial dataset supplied by the organizers. The official Stage 1 inputs are separate. The newer simplified planning cells are also separate from the full factory; chapter 14 explains the boundary.

## 1. What the competition expects

Yes: Stage 2 is strongly focused on quantum/QUBO optimization of an extended scheduling problem. Section 5 asks teams to make the factory realistic while making the quantum solution compact, accurate and understood. It asks for reduction, algorithm comparisons and scaling on the extended model, a classical reference on the same model, and disclosure of any loss of optimum. Decomposition and partitioning are explicitly listed as legitimate directions.

It does not require a demonstrated quantum advantage or one quantum circuit containing every factory mechanism. A hybrid is legitimate. But a complex factory animation plus an unrelated quantum example is a weak response to the integrated-result requirement. The gap between our rich physical factory and the narrower problems our quantum circuits optimize is a real weakness. My earlier explanation understated this emphasis.

The current defensible claim is: an implemented factory with classical/hybrid dispatch, genuine local quantum experiments, and a separate extended planning formulation with reference checks. We cannot claim that quantum optimization currently produces our strongest factory outcomes.

Source: [challenge §5 and §11](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=2). These are competition requirements; the manufacturing numbers below are our chosen model parameters.

## 2. The actual task in one sentence

Given customer orders, raw materials, machines, workers, tools, transport robots and an electricity system, choose legal production actions over time so that as many complete pumps as possible are shipped, with as little lateness and cost as possible, while reacting to disruptions as they become known.

The main pressure benchmark starts at minute zero with **24 known pump orders** and runs for **96 simulated hours**, or **5,760 one-minute steps**. It does not begin from an independently generated factory-in-progress snapshot. The 12-, 16- and 32-order experiments change the initial workload; some also change the horizon. The 32-order successful stretch examples use 240 hours.

Stage 1 instead gives two tiny fixed flow shops and asks only for makespan. There are no transport robots, workforce calendars, matched assembly, stock failures or electricity system in those official inputs.

### Input, decision and outcome are different things

|Kind|Examples|Meaning|
|---|---|---|
|Fixed input parameter|15 machines; milling takes 90 min; grid cap 90 kW|The controller must work with this number; it does not choose it during the run|
|Decision|Which ready part to prioritize; which mill to use; when to start|A choice the control system can influence|
|Random future event|Whether F2 fails; whether an inspection fails|An outcome the controller cannot choose or secretly read in advance|
|Changing state|Machine busy until minute 420; robot battery 70%; two blanks left|The information that changes after decisions and events|
|Measured result|23 pumps shipped; deadline debt; electricity bill|What we calculate from the resulting execution|

Not every possible decision is globally optimized. Many are made by deterministic rules inside our current controller.

## 3. What enters: orders and stock

An **order** is a customer request for one finished pump. An order is not a machine operation. Each order has an identity, release time, due time, material family and precision requirement.

Initial order release times cycle through **0, 2, 4 and 6 hours**. Due times cycle through **40, 46, 52, 58, 64 and 70 hours**. Families cycle through alloy A, B and C. Every fourth initial order requires precision manufacturing/inspection. These cycles repeat as order count increases.

For example, the first order P01 is released at hour 0 and due at hour 40. P02 is released at hour 2 and due at hour 46. These dates are fixed inputs, not answers found by the optimizer. Due means the desired shipment time; the 96-hour horizon is when evaluation stops.

The **STOCK** area on the drawing is the raw-material store in Hall A, called `RAW_A` in the code. It initially contains:

|Raw material|Initial quantity|Normal later delivery|
|---|---:|---:|
|Housing blanks|30|4|
|Rotor blanks|30|4|
|Flange blanks|30|4|

A blank is an unfinished piece of material. Ninety blanks are not ninety pumps: one pump needs one of each type. When an eligible component is released into production, it consumes one corresponding blank. Replacement components need additional blanks.

At 24 orders, nominal production uses 24 of each type, leaving six of each before urgent orders or replacements. At 32 orders, the initial 30 cannot cover all demand even without defects. The delivery supplies four of each at hour 30, or hour 39 under supply stress. There is no unlimited emergency material purchase.

## 4. Follow one pump through production

Each pump needs **its own housing, rotor and flange**. Their identities matter: P01's assembly cannot simply consume P02's rotor. The three component chains can progress in parallel, but operations within each chain must occur in order.

The following times are standard processing on normal-speed machines, before setup, transport, queueing, breaks or rework:

|Component or stage|Required operation sequence|Standard processing minutes|
|---|---|---|
|Housing|Turn → mill → wash → heat → inspect|60 + 90 + 30 + 120 + 45 = 345|
|Rotor|Turn → heat → mill → wash → inspect|60 + 120 + 75 + 30 + 45 = 330|
|Flange|Mill → weld → wash → inspect|60 + 60 + 30 + 45 = 195|
|Finished pump|Assemble matching components → inspect|60 + 45 = 105|

There are **16 nominal operations per pump**: five housing, five rotor, four flange, assembly and final inspection. For 24 orders that is 384 nominal operations. Extra setups, trips, maintenance, repairs and replacement recipes add activity beyond those 384.

The sum above is 975 processing minutes per ordinary pump. That is not its elapsed completion time: component chains can overlap, while shared resources and waiting can delay them. Even the idealized longest recipe chain, 345 + 105 = 450 min, ignores substantial constraints and is not a checked feasible schedule.

All three components must pass their component inspections and physically arrive at the selected assembly station. Assembly consumes them and creates the assembled pump. The pump then needs final QA and an AGV trip to `SHIP_B`, the shipping area in Hall B. Only the recorded shipment fulfills the order. Assembly completion and final inspection completion are earlier milestones.

## 5. What each machine does

The letters on the map name processes. The number distinguishes parallel machines of the same type.

|Labels|Plain meaning|Hall|Ordinary process power|Useful detail|
|---|---|---|---:|---|
|T1, T2|Lathes: turn a rotating blank into shape|A|9 kW|Housing/rotor turning normally takes 60 min|
|F1, F2|Mills: remove material to create shapes/features|A|12 kW|Housing 90 min, rotor 75, flange 60|
|F3|An alternative milling machine|B|12 kW|Takes 1.25 times the normal milling duration, rounded up|
|S1, S2|Welding stations|B|10 kW|Flange welding normally takes 60 min|
|WASH1, WASH2|Clean parts|A / B|4 kW|30 min|
|H1, H2|Heat-treatment furnaces|A / B|16 kW|120 min; compatible same-family batches up to four|
|QA1, QA2|Quality inspection stations|A / B|3 kW|45 min normally; precision takes 68 min and 3.6 kW|
|A1, A2|Assembly stations|B|4 kW|Join the matched housing, rotor and flange in 60 min|

There are 15 machines in total. A process cannot be moved to an arbitrary machine: a lathe does not become a welder. Alternative milling, washing, heat and inspection stations create routing choices. F3 is slower but may save cross-hall travel or avoid a queue.

Apart from declared heat batches, a machine runs one operation at a time. A finished part left at its output can keep the machine blocked even after processing ends.

### Modes change the tradeoff

Turning and milling offer standard, eco and turbo modes. Eco takes 1.5 times as long and uses 65% of standard power. Turbo takes 75% of the time, uses 150% of the power, increases wear and has greater manufacturing defect risk. Integer durations round up. Welding/assembly have a careful mode that takes 1.5 times as long and uses 80% of ordinary power. QA has standard or precision modes; precision takes 1.5 times the standard duration.

For a normal lathe operation, standard is 60 min at 9 kW; eco is 90 min at 5.85 kW; turbo is 45 min at 13.5 kW. Slower eco processing does not imply a proportionally smaller energy bill because it runs longer. Precision orders disallow turbo turning/milling and require precision QA.

## 6. Workers and setups: why an idle machine may not start

There are ten workers, each with specified skills. W01–W04 work 00:00–08:00, W05–W07 work 08:00–16:00, and W08–W10 work 16:00–24:00. These calendars repeat daily. Each shift includes two 30-minute breaks, starting 3 h 30 min and 6 h 30 min after shift start. Thus ten workers do not mean ten available people at every moment.

|Worker|Skills|
|---|---|
|W01, W05, W08|Setup, machining, maintenance|
|W02|Welding, setup|
|W03|QA, assembly|
|W04|Machining, assembly, QA|
|W06, W09|Welding, assembly|
|W07, W10|QA, assembly, setup|

Turning, milling, washing and heat treatment require **five minutes of start attendance**. After that the worker can leave while the machine continues. Welding, QA and assembly require **full processing attendance**. The required attendance must fit the worker's shift and avoid breaks. Automatic machining may continue across a break once legal tending ends. Workers take two minutes to change halls; worker walking is modeled separately from AGV lane reservations.

The machine also remembers the last material family. Same-family work needs zero changeover; A↔B costs 30 min; switching to or from C costs 45 min. The machine is unavailable during this setup. Qualified setup attendance is required in the full factory, sometimes from the same worker and sometimes a second person. An unused machine, free material and a machining worker still may be insufficient if no setup-qualified person is available.

## 7. Tools, batches, wear and finite space

Milling requires a portable milling kit; welding requires a welding fixture; inspection requires a calibration kit. We have **two milling kits, two welding fixtures and one calibration kit** initially. Their physical locations matter. AGVs move them, competing with part deliveries. Two QA machines do not initially give two simultaneous equipped inspections when the one calibration kit is the limiting resource.

Tools have 600 processing minutes of life and take 60 min to service, with appropriate worker attendance. Machines have a separate wear limit of 1,050 standard wear units and 75-minute maintenance. Eco/turbo modes change wear accumulation. Tool servicing and machine maintenance are different activities.

Heat treatment can combine up to four compatible same-family parts. A batch is one shared furnace occupation, rather than four separate 120-minute furnace runs. Waiting to fill a batch can save capacity but delay an urgent component.

Input buffers hold two parts at ordinary machining/welding/washing stations, four at heat/QA stations, and six at assembly. A destination slot is reserved before a part trip begins. Completed outputs can block machines until AGV collection. We therefore cannot plan unlimited future deliveries into a station that has nowhere to put them.

One extra calibration kit may be rented for 150 model-currency units, arriving eight hours after the request, under a 250-unit investment budget. This is a tool rental, not an additional machine.

## 8. AGVs, the single lane, and why transport creates queues

An **AGV** is an automated guided vehicle: a small transport robot. Four robots share the factory. Each carries one part or one portable tool at a time. A robot first travels empty to the pickup, loads the item, travels with it and unloads it. Those steps consume time; its battery also limits which trips it can accept.

The transport graph has one-minute station-to-hub edges and a four-minute edge connecting Hall A's hub to Hall B's hub. Loading and unloading each add one minute. An otherwise clear loaded station-to-station trip within a hall takes four minutes; one across halls takes eight. Empty repositioning, traffic and charger waits add time. The drawing is schematic: pixel distance does not determine travel duration.

**SINGLE LANE** means the bridge admits one robot at a time, in either direction. For example, a crossing from minute 100 to 104 prevents a conflicting crossing before minute 104. A robot returning empty occupies it too. Tool deliveries also use it. Four robots therefore cannot provide four simultaneous cross-hall trips. Every modeled road edge has capacity one; the bridge is especially important because all cross-hall trips share it.

At most 15 four-minute bridge crossings fit in an hour even before other constraints. That is a crossing bound, not 15 finished pumps per hour: a pump can require several component/tool crossings, plus empty repositioning. The actual impact depends on chosen routes and which resources are on each side.

This creates the tradeoff behind F3: milling in B takes longer, but may avoid a bridge trip or a congested A-side queue. Conversely, moving a part to a nominally free machine may be worse once travel and tooling are counted.

## 9. CHARGE A and CHARGE B: robot charging bays

These labels mean **a robot charger in Hall A and a robot charger in Hall B**. They do not mean two electrical grids, two production processes or two factory storage batteries. Each bay accommodates one charging robot at a time. A charging robot cannot simultaneously carry a part.

In the numerical model a robot's battery has 160 charge units, equivalent to 0.8 kWh; it starts with 120 units, or 75%. Empty travel consumes one unit per minute of movement; loaded travel consumes two. The controller preserves enough charge to reach a charger after a delivery.

The current charging rule considers idle robots below 90 units, sends them to a suitable available bay and charges to full at 12 units per minute, rounding duration up. Each charging robot draws 4 kW from the factory electrical system. The stored-energy rate is approximately 3.6 kW before saturation/rounding; charging is not free energy. The internal units are synthetic model choices, not measured vehicle specifications.

If both charging bays are occupied, another low-battery robot may wait. If two robots charge together they add 8 kW to factory demand. Under grid stress, this competes with starting production equipment.

## 10. Grid, solar and the stationary battery

The factory's electricity system is separate from the robots' individual batteries. It supplies the machines, building load and robot chargers.

**kW is power:** the rate of using electricity at a moment. **kWh is energy:** power accumulated over time. A 12 kW mill running for one hour uses 12 kWh. Its 90-minute housing operation uses 18 kWh in standard mode, before setup and other loads.

|Electrical quantity|Our model's value|Meaning|
|---|---:|---|
|Building base load|12 kW|Consumption even when production is idle|
|Normal grid limit|90 kW|Maximum permitted external power import at a time|
|Stressed grid limit|45 kW|Reduced limit during the supply-stress event|
|Solar maximum|16 kW|Local generation, varying with time of day|
|Stationary battery capacity|40 kWh|Energy storage for the factory|
|Initial stored energy|10 kWh|Battery charge at the beginning|
|Minimum stored energy|2 kWh|Lower operating limit|
|Required ending energy|At least 10 kWh|Cannot improve results by leaving a depleted battery|
|Battery charge action|10 kW draw|Stores energy at an effective 9 kW rate|
|Battery discharge action|9 kW output|Consumes stored energy at an effective 10 kW rate|

### What solar does

Solar is an assumed local photovoltaic supply. It follows a deterministic daily curve: zero overnight, positive from 06:00 to 18:00, peaking at 16 kW at noon. There are no random cloud forecasts in this version. Solar reduces the electricity the factory needs to import. Surplus that cannot be used or stored is curtailed; it is not sold for revenue.

### What the grid limit does

The limit is on instantaneous imported power, not total energy over the entire run. A 90 kW cap is not a stock of 90 kWh that gets used up. Once one machine finishes, the freed power can support another start.

At each minute the electrical balance is:

```text
load = building base load + active operation loads + robot charging loads
grid import = max(0, load - solar + stationary charging - stationary discharge)
grid import must not exceed the current grid cap
```

Illustrative arithmetic: if total load is 60 kW and solar is producing 10 kW, we need 50 kW from elsewhere. That is within a 90 kW grid limit. Under a 45 kW limit, 9 kW of battery output would reduce import to 41 kW, if stored energy and all other rules permit. The battery cannot rescue an arbitrarily large overload: its discharge power is bounded as well as its stored energy.

### What the battery does in our actual controller

It can move some energy between times, absorb charging losses and cover limited peaks. The current implementation applies a simple automatic rule: discharge for an excess over the grid cap if charge permits; otherwise charge when headroom permits and it is before 06:00 or below the ending-charge target. It is **not** a globally optimized battery-arbitrage schedule.

Machine-start guards are conservative: they generally leave an 8 kW reserve for robot charging and do not fully exploit forecast solar/battery flexibility. Thus an electrically possible action under the balance equation may still be rejected by our controller. This is a distinction between physical feasibility and the policy's decisions.

### What tariffs and carbon do

Grid electricity costs 0.34 model-currency units/kWh from 08:00 to 18:00 and 0.12 otherwise. Reported grid carbon intensity is 0.65 kg/kWh during those peak hours and 0.25 otherwise. The electricity bill sums imported energy times its tariff. Carbon sums imported energy times its carbon intensity.

These are synthetic assumptions. Electricity/rental cost enters our performance comparison; carbon is also reported. We did not implement a hard total electricity-bill or carbon budget. The hard energy constraints are power balance/capacity and the stationary battery's limits, including its ending charge.

## 11. Quality, stock loss and disruptions

Manufacturing accumulates defect risk depending on process, mode and wear. QA reveals whether a component passes. The controller cannot inspect its future quality draw before inspection. For example, the base turning risk contribution is 1% in eco, 2.5% in standard and 8% in turbo, with a wear contribution; several process risks combine across the route. These are not three fixed final-pump failure probabilities.

A failed inspection can cause one 45-minute repair followed by reinspection. Repair retains residual risk. A component that fails again is scrapped; an original component can trigger at most one replacement, released after a 180-minute lead time and needing a fresh blank and recipe. Replacements can also fail. A lost flange can therefore leave an otherwise completed housing and rotor unable to form a pump.

The hidden random outcomes use stable unit/attempt identities. Renaming a part does not legitimately obtain another draw. Uncertainty is part of the problem, not an optimization variable we can set to a favorable outcome.

|Reveal time|Event|Probability|Consequence|
|---|---|---:|---|
|Hour 12|F2 outage|35%|F2 unavailable from hour 12 to 18|
|Hour 24|Supply/grid stress|40%|Grid cap 45 kW until hour 36; material delivery delayed from hour 30 to 39|
|Hour 40|Urgent demand|50%|Two additional precision alloy-C pump orders, due at hour 72|

The three binary branches create eight exogenous scenarios, with further randomness from inspection. The controller can react once an event is revealed. It may simulate possible futures but must not use the actual hidden future as if known.

## 12. What counts as a good solution

First a run must satisfy the implemented physical and terminal constraints: no illegal overlaps or resource use, legitimate material identities, legal transport, and the battery's required ending state. A run can satisfy these rules and still ship few pumps.

Among valid executions, we compare the following in priority order:

1. Number of final orders not physically shipped by the horizon.
2. Total deadline debt: for shipped orders, time after due date; for unfinished orders, debt measured through the horizon.
3. Electricity-tariff plus rental cost. Carbon is reported alongside these.

This is lexicographic: fewer missing orders is prioritized over the secondary scores. It is not one unconstrained weighted energy-saving objective. The horizon does not replace due dates: all pumps shipped in 96 hours can still mean many late deliveries.

The solution is a sequence of actions and the resulting execution trace: operation starts/ends, workers, tool use, movements, quality events, electrical measurements and shipments. An independent checker reconstructs rule compliance; that is different from proving the policy globally optimal.

## 13. How the current factory controller makes decisions

At each simulated minute it processes completions and newly revealed events, releases eligible work with available stock, prioritizes parts, chooses routes, arranges tools and workers, assembles legal start offers, starts a compatible set, and updates transport, service and energy activity.

There is a hierarchy rather than one enormous quantum call. Macro settings influence admission, urgency and scarce-resource protection. CEM searches settings/time segments; PPO attempts to choose them from observed state; MPC simulates possible continuations. The underlying dispatcher still reacts to actual resource availability.

The best full-factory results are classical. Optional QUBO selectors replace a small start-selection step; they do not choose every route, battery action, tool trip and future event jointly.

## 14. The separate planning cell: what it keeps and removes

The newer deterministic cells schedule all 16 operations of each selected pump onto machines, workers and a discrete start grid. Their standard origin is factory hour 36, with the selected components treated as a hypothetical raw backlog. This is not a measured full-factory snapshot at hour 36.

|Condition|Full physical factory|Deterministic planning cell|
|---|---|---|
|Complete recipes and matching assembly|Yes|Yes|
|Machine choices, worker skills, shifts, breaks and attendance|Yes|Yes|
|Worker hall walking|Yes|Yes|
|Family setups|Machine and setup crew|Optional machine-only metric setup gaps|
|Transfer time|Actual scheduled AGV trips|Only machine-dependent minimum lag|
|AGV capacity, chargers, lanes and bridge queues|Yes|No|
|Buffers, output blocking and portable tools|Yes|No|
|Wear, maintenance, heat batching|Yes|No; heat operations individually scheduled|
|Manufacturing modes|Several choices|Fixed prescribed modes, required precision retained|
|Energy, materials and investment|Yes|No|
|Failures, repairs, urgent demand and disruptions|Yes|No|
|Completion event|Physical shipment|Final pump QA|

All mandatory cell operations must finish within its own horizon. For its standard pump DAG the score is:

```text
T = sum over pumps of weight * max(0, final-QA completion - due time)
score = (H + 1) * T + makespan
```

H and makespan are minutes. The multiplication ensures tardiness has priority over makespan, since makespan cannot exceed H. The combined score is not a number of minutes. Neither its optimum nor its lower bound automatically applies to the richer physical factory.

## 15. Encoding: the short answer about domain wall

**The current Stage 2 planning models are not domain-wall encoded.** They primarily use one-hot assignment or column choices. The conditional quantum experiments combine binary choices with a one-hot makespan register. Full-factory local QUBOs use action-selection bits and, when necessary, bounded-binary capacity slack.

Domain-wall code does exist in the project: it belongs to an earlier Stage 1 start-time formulation. The selected final Stage 1 formulation instead uses pairwise job-order bits.

|Project layer|What a bit means|Encoding actually used|
|---|---|---|
|Earlier Stage 1 time-indexed model|Start-time indicator or threshold|One-hot and domain-wall variants; earlier A used four domain-wall qubits|
|Selected Stage 1 compact model|Job A precedes job B|Pairwise order; one bit for A, three for B|
|Full-factory local selector|Start this offered operation/crew assignment now|Independent action bits; conflicts and bounded-binary slack where needed|
|Complete planning-cell QUBO|This operation uses this machine/worker/start|One-hot group per operation, plus one-hot makespan|
|Restricted component/operation pool|Choose this supplied candidate assignment or trajectory|One-hot candidate groups, plus one-hot makespan|
|Two-choice conditional quantum block|Choose option 0 or option 1|One binary bit per two-choice group, plus one-hot makespan|

QUBO is the quadratic objective form. One-hot, domain wall and pairwise order are ways of representing decisions inside that form. QAOA is a solver using a quantum circuit. These are different concepts, not interchangeable names.

## 16. One-hot: a worked start-assignment example

Suppose one housing-milling operation has three supplied candidate assignments. This is an illustrative group, not a recorded feasible schedule:

```text
x1 = 1: choose F1, worker W01, start minute 120
x2 = 1: choose F2, worker W01, start minute 120
x3 = 1: choose F3, worker W05, start minute 600
```

Exactly one is required. The bit strings 100, 010 and 001 choose the three options. 000 omits the operation; 110 schedules it twice. A penalty enforces the choice:

```text
P * (x1 + x2 + x3 - 1)^2
= P * (1 - x1 - x2 - x3 + 2*x1*x2 + 2*x1*x3 + 2*x2*x3)
```

The equality uses x*x=x for binary x. Every term is constant, linear or quadratic, so it is a QUBO. Legal choices cost zero penalty; omission or duplicate choices cost at least P.

Other operations have their own candidate groups. If a selected assignment x conflicts with assignment y because they overlap on F1, use the same worker concurrently, violate a predecessor/transfer lag or leave insufficient setup time, a term `P*x*y` penalizes choosing both. Individual impossible options, such as an unqualified worker or illegal attendance interval, are removed before construction.

There is also a one-hot makespan group. A bit says that the completion bound is a particular candidate time. Pair penalties forbid choosing a bound earlier than any selected operation ends. The objective rewards smaller legal bounds and smaller terminal tardiness. A penalty larger than a certified upper bound on feasible objective cost makes every global ground state legal and optimal for the declared feasible cell. A heuristic sample need not be a ground state, so decoding/checking is still required.

## 17. What domain wall would mean, and why the name does not fit our current model

For an ordered choice among four starts, one-hot uses four bits. A domain wall can use three monotone threshold bits:

|Chosen option|One-hot indicator|Domain-wall thresholds|
|---|---|---|
|First|1000|000|
|Second|0100|100|
|Third|0010|110|
|Fourth|0001|111|

With thresholds y0,y1,y2, recover the indicators by `x0=1-y0`, `x1=y0-y1`, `x2=y1-y2`, `x3=y2`. Valid thresholds satisfy y0≥y1≥y2. A penalty such as `P*y_next*(1-y_previous)` punishes a forbidden 0→1 increase. Our earlier Stage 1 implementation derives a sufficient wall penalty so that negative indicators from invalid strings cannot exploit conflict energy.

This saves one bit per d-choice group, replacing d by d−1; it does not generally turn d choices into log2(d) bits. It needs an ordered domain and a checked transformed objective/penalty argument. We have not implemented or validated this transformation across the current Stage 2 planning models. We cannot advertise its possible savings as measured results.

The two-choice substitution `x0=1-z, x1=z` is mathematically also the simplest two-state domain-wall mapping. In our current circuits it is used as direct binary/affine elimination of a two-choice group, not as a general multi-state domain-wall schedule encoding.

## 18. Local selectors and capacity slack

In a full-factory local QUBO, xA=1 means start offered operation A now. Unlike the mandatory planning groups, the selector can choose neither A nor B if starting nothing is the best compatible selection. Rewards encourage useful work; pair penalties prevent incompatible starts.

For an integer capacity, a nonnegative slack variable can turn an inequality into an equality. An illustrative resource budget of five and offers consuming three/four units gives:

```text
3*xA + 4*xB <= 5
3*xA + 4*xB + s = 5, with s in {0,1,2,3,4,5}
penalty = P * (3*xA + 4*xB + s - 5)^2
```

Our local builder represents s by bounded-binary weighted bits, removes redundant capacities and common integer factors, and uses pair conflicts without slack for applicable unit capacities. These extra bits count toward circuit size. They are not domain-wall bits. The integrated simulated QAOA selector caps at five total bits including slack; larger instances fall back to a recorded classical method.

The local reward is a scheduling priority surrogate, not the exact eventual shipment objective. A globally best local choice therefore need not be a globally best factory policy.

## 19. How thousands of planning bits became a 21-qubit circuit

They did not all fit simultaneously into 21 qubits. The process is decomposition and restriction:

1. Build a complete schedule classically and construct a finite candidate pool.
2. Keep most assignments fixed to the current schedule.
3. Select a small neighborhood and retain two choices for each selected operation.
4. Substitute each two-choice group by one binary variable.
5. Keep a small one-hot makespan register.
6. Run the conditional circuit, decode and independently check a proposal, and retain a valid non-worsening move.

A largest saved block has 16 binary operation choices and five one-hot makespan qubits: **21 logical qubits**. The rest of the 1,489-variable restricted master remains fixed. This experiment concerns the 32-operation cell. The separate 128-operation/6,046-variable pilot actually reached only six logical qubits and did not improve its parent.

The makespan qubits start in a state with exactly one excitation. An XY mixer moves that excitation among the register qubits, preserving the one-hot choice. Ordinary choice qubits use X mixing. This preserves the makespan register's form; it does not automatically enforce resource compatibility or solve the whole scheduling problem.

An invariant-sector classical simulator stores only the states reachable within that makespan sector. This reduces simulator memory without reducing the physical logical-qubit count. All reported circuits were simulated; no physical quantum computer was used.

## 20. What the results currently justify

|Evidence|Result|Boundary|
|---|---|---|
|Official Stage 1|4 h / 8 h optimum schedules from selected simulated QAOA|Tiny pairwise-order costs constructed exhaustively classically|
|Cheap full-factory controller, 12 orders / 96 h|94.98% weighted observed all-shipped frequency; mean misses 0.075|256 final tapes; due-date/cost optimality not established|
|Cheap full-factory controller, 24 orders / 96 h|Mean misses 10.0209; no all-shipped final tape observed|High-load control is weak; this alone does not prove physical infeasibility|
|Cheap full-factory controller, 32 orders / 240 h|91.02% weighted all-shipped frequency|Much longer horizon and substantial lateness|
|More expensive MPC|Improves 12/16-order missing counts; worsens 24|No universal quality gain; greater CPU cost|
|Raw deterministic planning cells|32/48/64-operation grid15 optima proved by classical CP|The declared simplified cells, not rich-factory optima|
|128-operation raw cell|Best score 13,941,691; lower bound 8,071,630|42.10% remaining relative bound interval|
|32-operation 21-qubit conditional search|1.93% improvement from its initial score|Classical proposal/uniform controls reach the same result|
|New planner connected to full factory|Mean misses worsened on fresh validation|Integration rejected; not promoted as our controller|

The 32-operation complete time-indexed QUBO has 5,443 variables and 1,664,149 couplers. A restricted operation pool has 1,489 variables and retains the same optimum on that one instance. At 128 operations the 6,046-variable restricted pool loses materially better raw schedules: its own optimum is 40.45% above the best known raw feasible score. A compact pool is not automatically a good pool.

There is no established quantum optimization advantage. The important achieved work is a working detailed model, explicit formulations, same-model checks, real circuit experiments and measured limits. The main unresolved issues are full-factory high-load performance and making quantum optimization useful on a coherent extended problem.

## 21. Map labels and symbols: quick reference

|Label|Meaning|
|---|---|
|STOCK / RAW_A|Hall A raw blanks and material entry point|
|SHIP / SHIP_B|Hall B destination whose completed delivery fulfills an order|
|CHARGE A / CHARGE B|One AGV charging bay in each hall|
|HUB_A / HUB_B|Junctions in the transport graph; not processing machines|
|TOOL_A / TOOL_B|Portable-tool starting/storage locations|
|T / F / S|Turning / milling / welding|
|WASH / H / QA / A|Washing / heat treatment / inspection / assembly|
|W01–W10|Worker identities, not machines or jobs|
|AGV|A transport robot|
|SOC|State of charge: how much battery energy remains; two different battery systems use it|
|Grid|External electrical power imported by the factory|
|Solar|Local time-dependent electrical generation|
|Load|Current electrical demand before subtracting solar or battery output|
|Horizon|The evaluation cutoff; not an order's due date|
|One-hot|Exactly one selected indicator among a group|
|Domain wall|Ordered choices represented by monotone threshold bits|
|QUBO|A quadratic function of binary variables, usable with classical or quantum solvers|
|QAOA|A quantum/classical variational algorithm used to sample candidate bit strings|
|CP-SAT|A classical constraint-programming solver used for scheduling references|

## 22. Source map and reading order

Read this document for the problem and actual encoding. Then use [the current complete research explanation](STAGE2_CURRENT_EXPLAINED.md) for the fuller result tables and proof scopes. [The methods course](learning-methods/index.html) explains general QUBO/quantum mathematics; it is not the specification of this factory.

|Subject|Owning source|
|---|---|
|Official competition requirements|[Challenge PDF](../Quantum_Hackathon_2026_ERP_Challenge.pdf)|
|Chosen factory numerical tables|[Runtime specification](../stage2/spec.py), [input blueprint](../instances/stage2/metaltech_pressure.json)|
|Actual events, transport, charging and energy rules|[Factory engine](../stage2/engine.py)|
|Physical rule checking|[Independent checker](../stage2/check.py)|
|Earlier Stage 1 domain-wall transformation|[Stage 1 builder](../solver/stage1.py)|
|Selected compact Stage 1 pairwise order|[Sequence model](../solver/sequence.py)|
|Local action QUBO and bounded-binary slack|[Local QUBO builder](../stage2/qubo.py)|
|Complete deterministic planning-cell assignments|[Window QUBO](../stage2/window_qubo.py)|
|Restricted operation columns|[Candidate generation](../stage2/operation_columns.py), [compiler](../stage2/operation_qubo.py)|
|Binary choices and one-hot register|[Trajectory model](../stage2/trajectory_qubo.py), [mixer](../stage2/trajectory_mixer.py)|
|Sector simulation|[Sector simulator](../stage2/sector_mixer.py)|
|Full-factory measured results|[Results document](STAGE2_RESULTS.md)|
|Planning experiment details|[Planning-core evidence](STAGE2_PLANNING_CORE.md)|

Numbers above describe the fine one-minute runtime profile. The original blueprint stores many durations in 15-minute ticks, so reading its raw integers without the expansion in spec.py gives the wrong physical times. Road-edge and worker-walk times have their own explicit runtime values. This document is a source-grounded explanation, not a claim of industrial calibration or a new optimization result.
