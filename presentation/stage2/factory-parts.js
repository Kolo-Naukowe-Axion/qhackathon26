import {partGlyph} from './factory-story.js';

const kinds=new Set(['housing','rotor','flange','pump']);
export function unitKind(id){
 const kind=String(id??'').split('/')[1]??String(id??'').split('-').at(-1);
 return kinds.has(kind)?kind:null;
}
export const operationProgress=(op,tick)=>Math.max(0,Math.min(1,(tick-op.start)/Math.max(Number.EPSILON,op.end-op.start)));

// Illustrative bench positions, synchronized to the recorded assembly interval.
// The finished pump replaces its parents only when that operation has ended.
export function assemblyPosition(index,count,progress){
 const p=Math.max(0,Math.min(1,progress)),ease=p*p*(3-2*p);
 const spread=count>1?index/(count-1)*2-1:0;
 return [spread*(25-17*ease),-17-(1-Math.abs(spread))*5+ease*3];
}
export function stationPieces(machine,state,tick){
 const op=state.active.find(row=>row.machine_id===machine.id&&(!row.kind||row.kind==='process'));
 if(op){
  const ids=op.process==='ASSEMBLY'&&op.parent_unit_ids?.length?op.parent_unit_ids:[op.unit_id];
  return ids.filter(id=>unitKind(id)).map((id,index)=>({id,kind:unitKind(id),assembly:op.process==='ASSEMBLY',index,count:ids.length,progress:operationProgress(op,tick)}));
 }
 const output=state.completed.filter(row=>row.machine_id===machine.id&&(!row.kind||row.kind==='process')&&state.location.get(row.unit_id)===machine.id).sort((a,b)=>b.end-a.end)[0];
 return output&&unitKind(output.unit_id)?[{id:output.unit_id,kind:unitKind(output.unit_id),assembly:false}]:[];
}
export function pieceTransform(piece,process){
 const [x,y]=piece.assembly?assemblyPosition(piece.index,piece.count,piece.progress):({T:[4,-25],F:[0,-19],S:[0,-12],WASH:[0,-23],HEAT:[0,-23],QA:[0,-9],ASSEMBLY:[0,-15]}[process]??[0,-15]);
 return `translate(${x} ${y}) scale(${piece.assembly ? .48 : .61}) translate(-18 -18)`;
}
export const glyphBody=kind=>partGlyph(kind).replace(/<svg[^>]*>|<\/svg>/g,'');
