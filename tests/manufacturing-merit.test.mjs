import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {attachMeritPlans,capacitySensitivity} from '../presentation/manufacturing/merit-model.js';
import {checkedCase} from '../presentation/manufacturing/model.js';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(readFileSync(new URL(p,root)));
const merit=read('presentation/manufacturing/merit-data.json');
test('quantum table reports valid encoded minima rather than raw objective coincidences',()=>{
 const lease=merit.quantum.filter(r=>r.case==='heat-lease-32');
 assert.deepEqual(lease.map(r=>r.methods.uniform_onehot.pool_optimal),[3,0,0]);
 assert.deepEqual(lease.map(r=>r.methods.qaoa_xy.pool_optimal),[3,3,3]);
 const ui=readFileSync(new URL('presentation/manufacturing/merit.js',root),'utf8');
 assert.match(ui,/encoded optimum runs/);
 assert.match(ui,/valid completion register and energy equal to the pool reference/);
});
test('merit evidence anchors exact source artifacts and complete checked recipe previews',()=>{
 for(const [p,h]of Object.entries(merit.source_sha256))assert.equal(createHash('sha256').update(readFileSync(new URL(p,root))).digest('hex'),h,p);
 const data=read('presentation/manufacturing/data.json');attachMeritPlans(data.cases,merit);
 for(const c of Object.values(data.cases))checkedCase(c);
 const recovered=data.cases['heat-lease-32'].plans.filter(p=>['enriched_reference','deadline_reference','recipe_qaoa'].includes(p.id));
 assert.equal(recovered.length,3);assert.ok(recovered.every(p=>p.check.weighted_terminal_tardiness===0&&p.plan.length===32));
 assert.equal(merit.baseline.selected_sequence_bits,3);
 assert.equal(merit.realism.feature_ablations.length,6);
 assert.equal(merit.realism.feature_ablations.find(r=>r.variant==='continuous_worker_calendars').support_complete.variables,9322);
});
test('browser economics agrees with exact Python example and does not confuse failed recovery with value',()=>{
 const actual=capacitySensitivity(merit.economics.records),expected=merit.economics.illustrative_repeated_exposure;
 assert.ok(Math.abs(actual.feeThreshold-expected.maximum_event_fee.value)<1e-9);
 assert.ok(Math.abs(actual.present-expected.present_value_of_net.value)<1e-8);
 assert.ok(Math.abs(actual.purchase-expected.maximum_upfront_purchase_price.value)<1e-8);
 assert.equal(capacitySensitivity(merit.economics.records,{probability:0}).annual,-50);
 assert.equal(capacitySensitivity(merit.economics.records,{variant:'replacement_original_pool'}).saved,0);
 assert.throws(()=>capacitySensitivity(merit.economics.records,{probability:2}));
 assert.throws(()=>capacitySensitivity(merit.economics.records,{lateRate:NaN}));
 const missing=structuredClone(merit.economics.records);delete missing.outage_complete.profile_sha256;delete missing.replacement_complete.profile_sha256;
 assert.throws(()=>capacitySensitivity(missing));
});
