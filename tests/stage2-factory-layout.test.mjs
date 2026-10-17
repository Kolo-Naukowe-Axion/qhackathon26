import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {positions,dockPoint} from '../presentation/stage2/factory-layout.js';
import {transportPath} from '../presentation/stage2/factory-motion.js';
const machines=['T1','T2','F1','F2','WASH1','H1','QA1','F3','S1','S2','WASH2','H2','QA2','A1','A2'];
const intersects=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
const body=id=>{const [x,y]=positions[id];return {left:x-44,right:x+45,top:y-49,bottom:y+25};};
test('machine labels and solid artwork leave the shared aisle clear',()=>{
 for(const id of machines){const [x,y]=positions[id],art=body(id),label={left:x-49,right:x+49,top:y+39,bottom:y+69};
  assert.ok(art.bottom<243||art.top>277,id+' artwork crosses the aisle');
  assert.ok(label.bottom<243||label.top>277,id+' label crosses the aisle');
  for(const other of machines.filter(other=>other!==id))assert.equal(intersects(label,body(other)),false,id+' label covers '+other);
 }
});
test('docked robots clear every machine body and the stock, shipping and charger artwork',()=>{
 const stationaryArt=[...machines.map(body),{left:25,right:73,top:295,bottom:360},{left:1080,right:1158,top:390,bottom:450},{left:37,right:72,top:125,bottom:172},{left:1102,right:1137,top:125,bottom:172}];
 for(const id of [...machines,'RAW_A','SHIP_B','CHARGE_A','CHARGE_B','TOOL_A','TOOL_B']){
  const [x,y]=dockPoint(id),robot={left:x-17,right:x+17,top:y-17,bottom:y+17};
  for(const art of stationaryArt)assert.equal(intersects(robot,art),false,id+' dock covers equipment');
 }
});
test('real transport legs never send a robot through solid machine artwork',()=>{
 const trace=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/tool-homes-train0-12.json',import.meta.url)));
 const collisions=[];
 for(const move of trace.moves){
  const path=transportPath(move,dockPoint);
  for(let i=1;i<path.length;i++){
   const [a,b]=[path[i-1],path[i]],swept={left:Math.min(a[0],b[0])-17,right:Math.max(a[0],b[0])+17,top:Math.min(a[1],b[1])-17,bottom:Math.max(a[1],b[1])+17};
   for(const id of machines){
    const [x,y]=positions[id],label={left:x-49,right:x+49,top:y+39,bottom:y+69};
    if(intersects(swept,body(id))||intersects(swept,label))collisions.push(move.id+' / '+id);
   }
  }
 }
 assert.deepEqual([...new Set(collisions)],[]);
});
