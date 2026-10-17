export const INSTANCES={
 A:{machines:['Turning','Milling'],jobs:[{id:'Z1',durations:[2,1]},{id:'Z2',durations:[1,2]}]},
 B:{machines:['Turning','Milling','Welding'],jobs:[{id:'Z1',durations:[2,1,2]},{id:'Z2',durations:[1,2,1]},{id:'Z3',durations:[2,2,1]}]},
};
export const permutations=ids=>ids.length?ids.flatMap((id,i)=>permutations(ids.filter((_,j)=>i!==j)).map(rest=>[id,...rest])):[[]];
export function earliestSchedule(instance,order){
 const available=instance.machines.map(()=>0),operations=[];
 for(const id of order){
  const job=instance.jobs.find(row=>row.id===id);let previous=0;
  job.durations.forEach((duration,machine)=>{const start=Math.max(previous,available[machine]),end=start+duration;operations.push({job:id,machine,start,end,duration});available[machine]=end;previous=end;});
 }
 return {operations,makespan:Math.max(0,...available)};
}
