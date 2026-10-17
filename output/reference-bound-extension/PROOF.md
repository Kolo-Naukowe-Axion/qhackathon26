# Scope-guarded prefix and hall-walk union argument

This is an arithmetic lower bound for the unchanged deterministic automatic-attendance reference, not the flagship factory. The four-pump instance has canonical numerical digest `3c6bda8bbf315951447394c68053894ff4a756be1c63f826de7c58739b5c3f7e`. The model/physical source hashes, precise numerical guards and witness checks are recorded in `bound.py` and `report.json`. No CP or factory execution is performed by this extension. The original 1480 certificate and solver-reported bounds remain unchanged.

For `n` pumps in this guarded family, required worker attendance is `350n`. The sole worker must attend all welding, QA and assembly, and the first five minutes of each automatic operation. All these intervals are mutually disjoint.

Let `A` be the union of required attendance intervals, and let `P = [0,64) \ A`. No initial raw operation can start before its four-minute loaded delivery. Every first operation takes 60 minutes, so none completes before 64. There is one T station and one F station, so at most one operation at each can start before 64. Their combined attendance is at most ten minutes. Thus `|P| >= 54`.

A productive B excursion is a maximal worker visit to hall B containing required welding or assembly. At departure from A, accepted unconsumed components can occupy only three reserved assembly input positions and one held QA output. In-flight accepted deliveries already reserve assembly capacity. No new QA acceptance can occur while the sole fully attending QA worker is in B. Starting two assemblies would consume six distinct accepted components; at most four are available, so at most one assembly starts per productive excursion. The first productive excursion must weld a flange before any assembly is possible. Consequently there are at least `n+1` productive B excursions.

Select the outward and return walks of any `n+1` such excursions, including the first. Their union `R` has measure `4(n+1)`, since each hall walk lasts two minutes. They are mutually disjoint, disjoint from `A`, and finish before the last required full pump QA. All selected walks except the first outward walk occur after the first required B operation, hence after 64.

The only possible overlap of `P` and `R` therefore has measure `o <= 2` and belongs to the first selected outward walk. If `o=0`, there is no overlap to compensate. Otherwise let `b` be that walk's arrival time. Its start is below 64, so `b <= 66`. The first required B operation is welding: first flange F cannot finish before 64, and its loaded F-to-S transfer takes eight more minutes. Therefore no required B attendance starts before 72. By definition of this productive excursion, the worker remains in B from `b` until its first B operation; there is no intervening return walk or required A attendance.

The interval `G = [max(64,b),72)` is consequently disjoint from `P`, `A` and the selected walks. Its measure is at least six, hence at least `o`. Therefore

```text
|P union R union G| >= |P| + |R| - o + |G|
                   >= 54 + 4(n+1).
```

This union argument permits arbitrary unproductive early walks. Those may occupy part of `P`; they are not incorrectly treated as literal nonwalking idle, nor subtracted a second time.

After the last required processing completion, which must be a full pump QA, that pump still needs eight minutes of loaded shipping. This final interval is disjoint from every counted attendance/walk/prefix interval. If `T` is the last shipment time,

```text
T >= 350n + 54 + 4(n+1) + 8 = 354n + 66.
```

At `n=4`, this gives **1482**, two minutes above the earlier 1480 arithmetic certificate. It adds no per-pump join, transport or idle gaps that could overlap other work. In particular, it does not add the last component-to-assembly or assembly-to-QA transfer gaps separately.

Three independent tests check the exact fixture, six changed-premise rejections, and overlap compensation for 400 integer/fractional walk starts. Every one of 26 locally retained complete, valid automatic-scale15 reference traces within the guards passes fresh physical replay and lies above the bound. The smallest retained makespans for 1/2/3/4 pumps are 566/863/1191/1567. Full-attendance and compressed-time references are explicitly outside this new bound's scope. Testing witnesses supports the implementation checks; the mathematical set argument above, not their finite enumeration, supplies the lower-bound proof.

The bound is primary reference makespan only. It does not certify secondary costs, extend a global gap to the flagship factory, change the running two-hour solver, or turn a nonzero remaining interval into a known exact gap.
