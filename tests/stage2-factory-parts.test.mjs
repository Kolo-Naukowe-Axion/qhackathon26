import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalizeTrace,snapshot} from '../presentation/stage2/model.js';
import {stationPieces,unitKind,assemblyPosition} from '../presentation/stage2/factory-parts.js';

const trace=normalizeTrace(JSON.parse(readFileSync(new URL('../presentation/stage2/traces/tool-homes-train0-12.json',import.meta.url))));
const assembly=trace.operations.find(op=>op.process==='ASSEMBLY');
const machine=trace.resources.machines.find(row=>row.id===assembly.machine_id);

test('assembly shows its actual parents until completion, then its physical output until pickup',()=>{
 for(const tick of [assembly.start,assembly.start+30,assembly.end-.001]){
  const pieces=stationPieces(machine,snapshot(trace,tick),tick);
  assert.deepEqual(pieces.map(row=>row.id),assembly.parent_unit_ids);
  assert.ok(pieces.every(row=>row.assembly&&row.kind!=='pump'));
 }
 const move=trace.moves.find(move=>move.unit_id===assembly.unit_id&&move.from===machine.id&&move.pickup_tick>=assembly.end);
 assert.equal(snapshot(trace,assembly.end).location.get(assembly.unit_id),move.agv_id);
 assert.equal(stationPieces(machine,snapshot(trace,assembly.end),assembly.end).some(piece=>piece.kind==='pump'),false);
 const delayed={...trace,moves:trace.moves.map(row=>row===move?{...row,start:row.start+5,pickup_tick:row.pickup_tick+5}:row)};
 const pieces=stationPieces(machine,snapshot(delayed,assembly.end),assembly.end);
 assert.deepEqual(pieces.map(row=>row.id),[assembly.unit_id]);
 assert.equal(pieces[0].kind,'pump');
 assert.equal(stationPieces(machine,snapshot(trace,move.pickup_tick),move.pickup_tick).some(piece=>piece.id===assembly.unit_id),false);
});

test('bench poses converge smoothly, stay bounded and reverse deterministically on seek',()=>{
 for(let index=0;index<3;index++){
  const start=assemblyPosition(index,3,0),end=assemblyPosition(index,3,1);
  assert.ok(Math.abs(end[0])<=Math.abs(start[0]));
  assert.deepEqual(assemblyPosition(index,3,-1),start);
  assert.deepEqual(assemblyPosition(index,3,2),end);
  for(let p=0;p<=1;p+=.01){const [x,y]=assemblyPosition(index,3,p);assert.ok(Math.abs(x)<=25&&y>=-22&&y<=-14);}
 }
 assert.equal(unitKind('P01/housing/1'),'housing');
 assert.equal(unitKind('fixture-rotor'),'rotor');
 assert.equal(unitKind('tool-17'),null);
});
