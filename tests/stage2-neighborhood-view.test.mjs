import test from 'node:test';
import assert from 'node:assert/strict';
import {summarizeNeighborhood,neighborhoodView} from '../presentation/stage2/neighborhood.js';
// Synthetic, test-only controller neighborhoods; no fixture is published as measurement.
function fixture(){
 const data={schema:'stage2-neighborhood-view.v1',role:'TRAIN',source_files_verified:true,final_policy_changed:false,complete_checked_grid:true,witnesses_complete_valid:true,source_stable:true,actual_grid_execution_count:12184,actual_oracle_replay_count:24,cpu_seconds:3600,wall_seconds:400,actions:Array.from({length:6},(_,i)=>({wip_limit:4+2*Math.floor(i/2),qa_guard_threshold:4*(i%2)})),contexts:[]};
 for(const orders of [12,16,24]){
  const radius=orders===12?1:2,original=Array(8).fill(0),schedules=[original];
  for(let p=0;p<8;p++)for(let a=1;a<6;a++){const s=[...original];s[p]=a;schedules.push(s);}
  if(radius===2)for(let p=0;p<8;p++)for(let q=p+1;q<8;q++)for(let a=1;a<6;a++)for(let b=1;b<6;b++){const s=[...original];s[p]=a;s[q]=b;schedules.push(s);}
  const variants=schedules.map((schedule,i)=>({variant_id:i,schedule,aggregate_key:[i,800,80]}));
  data.contexts.push({orders,radius,variant_count:variants.length,actual_rows:variants.length*8,invalid:0,complete_checked_neighborhood:true,fixed_variants:variants,original_common_fixed_variant:variants[0],best_common_fixed_variant:variants[0],offline_per_tape_oracle_aggregate_key:[0,800,80],per_tape:Array.from({length:8},(_,seed)=>({seed,lex_min:[0,100,10],lex_max:[100,100,10],original_key:[0,100,10],first_lexicographic_minimum_variant_id:0,schedule:original,distinct_physical_trajectories:1,original_physical_equivalent_variants:variants.length}))});
 }
 return data;
}
test('finite neighborhood view distinguishes common fixed control from hindsight and full optimum',()=>{
 const data=fixture();assert.equal(summarizeNeighborhood(data).valid,true);const html=neighborhoodView(data);
 assert.match(html,/common fixed schedule applies one unchanged/);assert.match(html,/offline oracle, not a deployable controller/);assert.match(html,/full 6⁸ controller domain/);assert.match(html,/No final policy is changed/);assert.match(html,/TRAIN 0–7/);
});
test('missing,invalid,duplicate or out-of-radius executions suppress every neighborhood minimum',()=>{
 for(const mutate of [d=>d.complete_checked_grid=false,d=>d.contexts[0].invalid=1,d=>d.contexts[1].fixed_variants.pop(),d=>d.contexts[1].fixed_variants[1].schedule=[...d.contexts[1].fixed_variants[0].schedule],d=>d.contexts[0].fixed_variants[1].schedule=Array(8).fill(5),d=>d.contexts[0].per_tape[0].seed=10000,d=>d.role='FINAL',d=>d.final_policy_changed=true]){
  const d=fixture();mutate(d);assert.equal(summarizeNeighborhood(d).valid,false);assert.match(neighborhoodView(d),/no partial minimum is shown/);
 }
});
test('hindsight and common-fixed summaries must agree with retained candidate keys and counts',()=>{
 for(const mutate of [d=>d.contexts[0].best_common_fixed_variant={...d.contexts[0].fixed_variants[0],aggregate_key:[-1,0,0]},d=>d.contexts[0].offline_per_tape_oracle_aggregate_key=[-1,0,0],d=>d.contexts[0].per_tape[0].original_physical_equivalent_variants=42,d=>d.contexts[0].per_tape[0].schedule=Array(8).fill(1)]){
  const d=fixture();mutate(d);assert.equal(summarizeNeighborhood(d).valid,false);
 }
});
test('sealed actual TRAIN landscape retains full domains, independent audit and common-vs-hindsight counts',async()=>{
 const {readFileSync}=await import('node:fs'),{createHash}=await import('node:crypto');
 const data=JSON.parse(readFileSync(new URL('../presentation/stage2/research/neighborhood-evidence.json',import.meta.url)));
 const result=summarizeNeighborhood(data);assert.equal(result.valid,true);
 for(const source of Object.values(data.sources))assert.equal(createHash('sha256').update(readFileSync(new URL('../'+source.path,import.meta.url))).digest('hex'),source.sha256,source.path);
 assert.deepEqual(result.contexts.map(c=>[c.orders,c.original_common_fixed_variant.aggregate_key[0],c.best_common_fixed_variant.aggregate_key[0],c.offline_per_tape_oracle_aggregate_key[0]]),[[12,0,0,0],[16,21,19,15],[24,76,76,69]]);
 assert.deepEqual(result.contexts.map(c=>c.necessary_bound_summary.primary_certified_tapes),[8,1,0]);
 assert.ok(result.contexts.every(c=>c.necessary_bound_summary.sum_missing_lower_bound===0&&c.necessary_bound_summary.secondary_gap===null));
 for(const c of result.contexts)for(const tape of c.per_tape)assert.equal(tape.distinct_objective_triple_count,tape.distinct_objective_triples.length);
 assert.equal(data.cost.allocated_cpus,32);assert.equal(data.cost.scheduler_elapsed_seconds,1511);assert.ok(Math.abs(data.cost.allocated_cpu_hours-1511*32/3600)<1e-10);
 assert.equal(data.cost.inherited_fit_episodes,9096);assert.equal(data.cost.inherited_validation_episodes,720);
});
test('reproducible landscape deep link opens the diagnostic at a declared load/tape',()=>{
 const previous=globalThis.location;globalThis.location={search:'?view=research&section=exact&landscape=1&landscape_orders=24&landscape_seed=7'};
 try{const html=neighborhoodView(fixture());assert.match(html,/<details class="reading-details" open>/);assert.match(html,/value="24" selected/);assert.match(html,/Hindsight winner for TRAIN 7/);}finally{if(previous===undefined)delete globalThis.location;else globalThis.location=previous;}
});
