export function attachMeritPlans(cases,merit){
 for(const row of merit.plans){
  const c=cases[row.case];if(!c||row.plan.length!==c.operations||!row.check.valid)throw Error('Incompatible merit plan');
  c.plans.push({...row});
 }
 return cases;
}
export function capacitySensitivity(records,{lateRate=10,eventFee=100,probability=.3,exposures=52,years=3,discount=.05,maintenance=50,installation=100,variant='replacement_complete'}={}){
 for(const v of [lateRate,eventFee,probability,exposures,years,discount,maintenance,installation])if(!Number.isFinite(v)||v<0)throw Error('Finite nonnegative assumptions required');
 if(probability>1||!Number.isInteger(exposures)||!Number.isInteger(years)||exposures<1||years<1)throw Error('Invalid probability or exposure horizon');
 const a=records.outage_complete,b=records[variant];if(!a||!b||!/^[a-f0-9]{64}$/.test(a.profile_sha256??'')||a.profile_sha256!==b.profile_sha256)throw Error('Cost profile mismatch');
 const saved=a.check.weighted_terminal_tardiness-b.check.weighted_terminal_tardiness;
 const operatingSaved=a.money.operating.value-b.money.operating.value;
 const feeThreshold=operatingSaved+saved*lateRate;
 const annual=exposures*probability*(feeThreshold-eventFee)-maintenance;
 let present=-installation,purchase=-installation;
 for(let t=1;t<=years;t++){present+=annual/(1+discount)**t;purchase+=(exposures*probability*feeThreshold-maintenance)/(1+discount)**t;}
 return {saved,operatingSaved,feeThreshold,eventNet:feeThreshold-eventFee,annual,present,purchase};
}
