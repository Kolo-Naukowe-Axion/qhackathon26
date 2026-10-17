// Narrative selects retained schedules. It never changes a model or solves one.
export const storySteps=[
 {id:'outage',case:'heat-outage-32',method:'raw_reference',label:'A furnace goes offline',tag:'THE DISRUPTION',title:'One furnace down.',copy:'Two pumps are due in 15 hours. With a furnace unavailable, even the complete reference schedule misses a deadline.'},
 {id:'capacity',case:'heat-lease-32',method:'raw_reference',label:'Make spare capacity available',tag:'THE OPPORTUNITY',title:'The deadline can be saved.',copy:'Extra heat capacity is available from hour 6. The complete reference finds a plan that finishes both pumps on time.'},
 {id:'restriction',case:'heat-lease-32',method:'pool_reference',label:'See what the compact model loses',tag:'THE MODELING TRAP',title:'The compact plan stays late.',copy:'The same spare capacity, but fewer scheduling choices. Even this pool’s exact optimum misses the recovery plan.'},
 {id:'enrichment',case:'heat-lease-32',method:'enriched_reference',label:'Keep the recovery choices',tag:'THE RECOVERY',title:'Better choices. Deadline saved.',copy:'Deterministic enrichment restores the on-time optimum at 2,078 bits. The complete optimization encoding uses 2,499.'}
];
export function selectedStory(caseId,method){return storySteps.find(s=>s.case===caseId&&s.method===method)??null;}
export function elapsed(minutes){const t=Math.floor(minutes+1e-7),h=Math.floor(t/60),m=t%60;return `${h}h ${String(m).padStart(2,'0')}m`;}
export const observations={
 outage:'H2 is unavailable for the whole planning window. The remaining heat capacity cannot keep both pumps within the 15-hour deadline.',
 capacity:'H3 becomes eligible at hour 6. Extra heat capacity allows a coordinated plan that finishes both pumps in 14h 15m.',
 restriction:'H3 is still available. The small pool retains its assignment rows, but loses other coordinated choices needed to recover the deadline.',
 enrichment:'Enrichment adds scheduling choices. Its certified pool optimum now matches the complete-model recovery: both pumps inspected by 14h 15m.'
};
