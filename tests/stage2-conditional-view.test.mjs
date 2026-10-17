import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {summarizeConditionalLeaves,conditionalLeaves} from '../presentation/stage2/conditional-leaves.js';
const source=()=>JSON.parse(readFileSync(new URL('../presentation/stage2/research/final-evidence.json',import.meta.url))).conditional_leaves;
test('observed branch table keeps32 environments, exact weights and horizon labels without population certainty',()=>{
 const data=source(),summary=summarizeConditionalLeaves(data);assert.equal(summary.valid,true);assert.equal(summary.groups.length,4);assert.ok(summary.groups.every(g=>g.leaves.every(l=>l.environment_tapes===32)));
 const stretch=summary.groups.find(g=>g.method_id==='selected-stretch-32');assert.equal(stretch.leaves[0].conditional_actor_averaged_means.missing_orders,0);assert.equal(stretch.leaves[0].all_fulfilled_by_tape.reduce((s,t)=>s+t.actor_mean_all_fulfilled,0),32);
 const html=conditionalLeaves(data);assert.match(html,/32\/32 observed all fulfilled/);assert.match(html,/Stretch32 · 240h/);assert.match(html,/descriptive associations, not causal/);assert.match(html,/does not establish true success probability one/);assert.ok(!html.includes('100%'));
});
test('missing cells, actor pseudoreplication, wrong branch weights and wrong reweighted outcomes suppress table',()=>{
 for(const mutate of [d=>d.groups[0].leaves.pop(),d=>d.groups[0].config.horizon=d.groups[0].config.horizon===5760?14400:5760,d=>d.groups[0].leaves[0].actor_seeds=[123],d=>d.groups[0].leaves[0].environment_tapes=96,d=>d.groups[0].actor_seeds=[900000,900001,900002],d=>d.groups[0].leaves[0].true_probability=[1,8],d=>d.groups[0].true_probability_reweighted_means.missing_orders=999,d=>d.groups[0].leaves[0].all_fulfilled_by_tape[0].actor_mean_all_fulfilled=.5,d=>d.groups[0].leaves[0].uncertainty_intervals=[0,1]]){
  const d=source();mutate(d);assert.equal(summarizeConditionalLeaves(d).valid,false);assert.match(conditionalLeaves(d),/suppressed/);
 }
});
