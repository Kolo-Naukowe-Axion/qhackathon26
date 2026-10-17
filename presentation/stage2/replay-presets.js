// These are the first predeclared final tapes, not outcomes chosen for the demo.
export const FINAL_REPLAYS=[
 {id:'final12',path:'./traces/final-first-leaf0-12-5760.json.gz',method:'static-grid-12',orders:12,hours:96},
 {id:'final32',path:'./traces/final-first-leaf0-32-14400.json.gz',method:'selected-stretch-32',orders:32,hours:240},
];
export const DEFAULT_REPLAY=FINAL_REPLAYS[0].path;
export function replayPreset(run){
 const context=run.provenance.viewer_replay;
 if(!context?.predeclared_first_tape)return null;
 return FINAL_REPLAYS.find(row=>row.method===context.selection?.method_id&&row.orders===context.selection?.config?.orders&&row.hours*60===run.horizon_ticks)??null;
}
