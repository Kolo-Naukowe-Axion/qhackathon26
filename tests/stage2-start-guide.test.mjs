import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateGuide,guideView,toyEnergy} from '../presentation/stage2/start.js';
const root=new URL('../',import.meta.url),read=p=>readFileSync(new URL(p,root)),data=JSON.parse(read('presentation/stage2/start-data.json'));
const state={chapter:'models',layer:'factory',step:0,bits:[1,1,0]};
test('guide anchors retained results without modifying either frozen export',()=>{
 assert.equal(validateGuide(data),data);assert.ok(data.no_factory_runs&&data.no_solver_runs);
 for(const[p,hash]of Object.entries(data.source_sha256))assert.equal(createHash('sha256').update(read(p)).digest('hex'),hash,p);
 assert.equal(createHash('sha256').update(read('presentation/stage2/research/final-evidence.json')).digest('hex'),'6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60');
 assert.equal(createHash('sha256').update(read('presentation/stage2/planning-data/evidence.json')).digest('hex'),'e89622edf009131d203982231eba968b2cc8b4e9a6cb30318b4ea4ba05177cff');
});
test('current factory examples preserve calendars, empirical probabilities and classical selection',()=>{
 const rows=data.selected_classical;assert.deepEqual(rows.map(r=>[r.orders,r.horizon_hours,r.environments]),[[12,96,256],[16,96,256],[24,96,256],[32,240,256]]);
 assert.equal(rows[0].all_shipped,.94984375);assert.equal(rows[0].mean_missing,.07500000000000001);
 assert.equal(rows[2].all_shipped,0);assert.equal(rows[3].all_shipped,.91015625);
 const html=guideView(data,{...state,chapter:'results'});
 assert.match(html,/preselected cheap classical/);assert.match(html,/0 observed/);assert.match(html,/240 h, not 96 h/);
 assert.match(html,/MPC improves fulfillment at 12 and 16.*regresses at 24/);assert.match(html,/not a claim that they beat every method/);
 assert.match(html,/863 \/ 1,191 minutes/);assert.match(html,/weighted score/);
 assert.match(html,/42.1%/);assert.match(html,/40.45%/);
});
test('all four explanation layers are separate and small quantum scopes cannot become whole-factory claims',()=>{
 for(const layer of ['stage1','factory','cell','reference']){const html=guideView(data,{...state,layer});assert.match(html,/Four layers/);assert.ok(!html.includes('undefined'));}
 assert.equal(data.stage1.A.jobs.length,2);assert.equal(data.stage1.B.jobs.length,3);
 assert.equal(data.quantum_scope.max_simulated_qubits,5);assert.equal(data.sector.max_qubits,21);
 assert.deepEqual(data.sector.qaoa_end,data.sector.proposal_end);assert.equal(data.sector.reference,908670);
 const html=guideView(data,{...state,chapter:'solve'});
 assert.match(html,/5 total bits/);assert.match(html,/21 logical qubits/);assert.match(html,/not that entire master/);
 assert.match(html,/No physical quantum computer was used/);
 const corrupt=structuredClone(data);corrupt.sector.qaoa_end[0]=0;assert.throws(()=>validateGuide(corrupt),/control claim/);
});
test('pump explanation preserves all sixteen operations and three matching assembly parents',()=>{
 assert.equal(data.recipe.length,16);const join=data.recipe.find(o=>o.id==='pump/step0');assert.deepEqual(join.predecessors,['housing/step4','rotor/step4','flange/step3']);
 for(let step=0;step<6;step++){const html=guideView(data,{...state,chapter:'pump',step});assert.match(html,/same order/);assert.match(html,/transfer lags/);assert.match(html,/No setup crew/);assert.match(html,/Final QA/);assert.ok(!html.includes('undefined'));}
});
test('QUBO educational penalty excludes shared-worker double booking and is labeled illustrative',()=>{
 const energies=Array.from({length:8},(_,i)=>({bits:[i&1,(i>>1)&1,(i>>2)&1],e:toyEnergy([i&1,(i>>1)&1,(i>>2)&1])}));
 assert.deepEqual(energies.toSorted((a,b)=>a.e-b.e)[0],{bits:[1,0,1],e:-16});
 assert.ok(energies.filter(r=>r.bits[0]&&r.bits[1]).every(r=>r.e>0));
 const html=guideView(data,{...state,chapter:'solve'});assert.match(html,/NOT MEASURED FACTORY DATA/);assert.match(html,/not a new solver result/);
});
test('guide is discoverable from factory, research and planning without taking over their navigation',()=>{
 for(const p of ['presentation/stage2/index.html','presentation/stage2/planning.html','presentation/stage2/research.js'])assert.match(read(p).toString(),/href="\.\/start\.html"/);
 assert.match(read('presentation/stage2/start.html').toString(),/\.\/start\.js/);
});
