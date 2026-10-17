import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {renderFactoryScene} from '../presentation/manufacturing/factory-scene.js';

const data=JSON.parse(readFileSync(new URL('../presentation/manufacturing/data.json',import.meta.url)));
const c=data.cases['heat-lease-32'];
const s=c.plans.find(p=>p.id==='raw_reference');
const station=(svg,id)=>svg.match(new RegExp(`data-machine="${id}" data-machine-state="([^"]+)"`))?.[1];

test('factory scene follows processing and attendance boundaries without mutating evidence',()=>{
 const before=JSON.stringify({c,s});
 const row=s.plan.find(r=>r.attended_end<r.end);
 const atStart=renderFactoryScene({c,s,tick:row.start,selectedOperation:row.operation,selectedOrder:'P01'});
 const afterAttendance=renderFactoryScene({c,s,tick:row.attended_end});
 const atEnd=renderFactoryScene({c,s,tick:row.end});
 assert.equal(station(atStart,row.machine),'active');
 assert.ok(atStart.includes(`data-active-operation="${row.operation}"`));
 assert.ok(atStart.includes(`data-attending-worker="${row.worker}"`));
 // This worker might attend another operation at that instant, so check the
 // station's subtree rather than suppressing the worker everywhere.
 const segment=afterAttendance.split(`data-machine="${row.machine}"`)[1].split('class="factory-station ')[0];
 assert.ok(segment.includes(`data-active-operation="${row.operation}"`));
 assert.ok(!segment.includes(`data-attending-worker="${row.worker}"`));
 assert.ok(!atEnd.includes(`data-active-operation="${row.operation}"`));
 assert.ok(atStart.includes('role="button"'));
 assert.ok(atStart.includes('factory-station--selected'));
 assert.equal(JSON.stringify({c,s}),before);
});

test('availability derives replacement release and calendars rather than an animation clock',()=>{
 const early=renderFactoryScene({c,s,tick:359});
 assert.equal(station(early,'H2'),'offline');
 assert.equal(station(early,'H3'),'future');
 assert.ok(early.includes('FROM 360m'));
 const variant=structuredClone(c);
 variant.problem.machines.H3.available=[[500,900]];
 const delayed=renderFactoryScene({c:variant,s:{plan:[]},tick:100});
 assert.equal(station(delayed,'H3'),'future');
 assert.ok(delayed.includes('FROM 500m'));
 assert.equal(station(renderFactoryScene({c:variant,s:{plan:[]},tick:900}),'H3'),'closed');
 assert.ok(!early.includes('data-vehicle'));
});

test('station progress is the literal interval fraction and labels remain textual',()=>{
 const row=s.plan.find(r=>r.machine==='H3');
 const svg=renderFactoryScene({c,s,tick:(row.start+row.end)/2});
 assert.ok(svg.includes('data-progress="0.500000"'));
 assert.ok(svg.includes('HEAT TREAT'));
 assert.ok(svg.includes('RUNNING'));
 assert.ok(svg.includes('Equipment layout is illustrative; processing and attendance follow the selected schedule.'));
 assert.ok(svg.includes('viewBox="0 0 1000 710"'));
 assert.ok(svg.includes('class="factory-heat-glow"'));
 assert.ok(svg.includes('@media(prefers-reduced-motion:reduce)'));
});

test('an unavailable machine can be selected without inventing an operation for it',()=>{
 const svg=renderFactoryScene({c,s,tick:360,selectedMachine:'H2',selectedOperation:s.plan[0].operation});
 const selected=svg.match(/class="factory-station [^"]*factory-station--selected" data-machine="([^"]+)"/g);
 assert.equal(selected.length,1);
 assert.ok(selected[0].includes('data-machine="H2"'));
 assert.equal(station(svg,'H2'),'offline');
});
