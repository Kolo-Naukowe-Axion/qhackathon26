/* Check the actual browser visual's pure maths against independent formulas. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const crypto = require('node:crypto');
const exportsHolder = {exports:{}};
const visualSource=fs.readFileSync(path.join(__dirname,'visuals.js'),'utf8');
vm.runInNewContext(visualSource,{module:exportsHolder,Math});
const {phaseState, blochState, registerState, qaoaState, sampleCounts, magnitudeSquared, energies} = exportsHolder.exports;
const near = (a,b) => assert(Math.abs(a-b)<1e-11,`${a} != ${b}`);
const norm = state => state.reduce((sum,z)=>sum+magnitudeSquared(z),0);
let phaseCases=0,registerCases=0,circuitCases=0,blochCases=0;
for(const p of [0,.01,.25,.5,.75,.99,1]) for(let theta=0;theta<=360;theta+=15) {
  const state=phaseState(p,theta);
  near(norm(state),1);near(magnitudeSquared(state[0]),p);near(magnitudeSquared(state[1]),1-p);
  phaseCases++;
}
// Compare Bloch probabilities with direct basis-change gates on amplitudes.
for(let theta=0;theta<=180;theta+=15) for(let phi=0;phi<=360;phi+=15) {
  const original=blochState(theta,phi),rotated=blochState(theta,phi,true);
  for(const result of [original,rotated]) {
    const {state:[a,b],r,plus}=result;
    near(magnitudeSquared(a)+magnitudeSquared(b),1);
    near(r.reduce((sum,value)=>sum+value*value,0),1);
    near(plus[0],((a.re+b.re)**2+(a.im+b.im)**2)/2);
    near(plus[1],((a.re+b.im)**2+(a.im-b.re)**2)/2);
    near(plus[2],magnitudeSquared(a));
    r.forEach((value,i)=>near(value,original.r[i]));
  }
  near(original.r[0],Math.sin(theta*Math.PI/180)*Math.cos(phi*Math.PI/180));
  near(original.r[1],Math.sin(theta*Math.PI/180)*Math.sin(phi*Math.PI/180));
  near(original.r[2],Math.cos(theta*Math.PI/180));
  blochCases++;
}
const initialBloch=blochState(90,45);
near(initialBloch.state[1].re,.5);near(initialBloch.state[1].im,.5);
near(initialBloch.plus[2],.5);near(initialBloch.plus[0],(1+Math.SQRT1_2)/2);near(initialBloch.plus[1],(1+Math.SQRT1_2)/2);
for(const [theta,phi,axis,expected] of [[0,0,2,1],[180,0,2,0],[90,0,0,1],[90,180,0,0],[90,90,1,1],[90,270,1,0]])near(blochState(theta,phi).plus[axis],expected);
for(let n=1;n<=4;n++) for(const mode of ['basis','uniform','weighted','correlated']) for(let selected=0;selected<2**n;selected++) {
  const state=registerState(n,mode,selected);
  assert.equal(state.length,2**n);near(norm(state),1);
  if(mode==='basis') state.forEach((z,i)=>near(magnitudeSquared(z),i===selected?1:0));
  if(mode==='uniform') state.forEach(z=>near(magnitudeSquared(z),1/(2**n)));
  if(mode==='weighted') {near(magnitudeSquared(state[n===1?0:1]),.75);near(magnitudeSquared(state[n===1?1:2**n-2]),.25);}
  if(mode==='correlated') {near(magnitudeSquared(state[0]),.5);near(magnitudeSquared(state.at(-1)),.5);}
  registerCases++;
}
const mul=(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]];
// Full 4x4 mixer matrix: matrix[y,x] = c^(2-d) * (-i sin beta)^d,
// where d is the Hamming distance between the two complete bitstrings.
for(let g=-8;g<=8;g++) for(let b=-8;b<=8;b++) {
  const gamma=g*Math.PI/8,beta=b*Math.PI/16;
  const phased=qaoaState(gamma,beta,1),mixed=qaoaState(gamma,beta,2);
  near(norm(phased),1);near(norm(mixed),1);
  phased.forEach(z=>near(magnitudeSquared(z),.25));
  for(let y=0;y<4;y++) {
    let expected=[0,0];
    for(let x=0;x<4;x++) {
      const xor=x^y,d=(xor&1)+((xor>>1)&1);
      let factor=[1,0];
      for(let k=0;k<2-d;k++)factor=mul(factor,[Math.cos(beta),0]);
      for(let k=0;k<d;k++)factor=mul(factor,[0,-Math.sin(beta)]);
      const amplitude=[.5*Math.cos(gamma*energies[x]),-.5*Math.sin(gamma*energies[x])];
      const contribution=mul(factor,amplitude);
      expected=[expected[0]+contribution[0],expected[1]+contribution[1]];
    }
    near(mixed[y].re,expected[0]);near(mixed[y].im,expected[1]);
  }
  circuitCases++;
}
for(const [beta,expected] of [[-Math.PI/4,[.5,.5,0,0]],[Math.PI/4,[0,0,.5,.5]],[0,[.25,.25,.25,.25]]]) {
  const state=qaoaState(-Math.PI/2,beta,2);
  state.forEach((z,i)=>near(magnitudeSquared(z),expected[i]));
}
const equal=qaoaState(0,0,0);let draws=0;
assert.deepEqual([...sampleCounts(equal,100,()=>((draws++)+.5)/100)],[25,25,25,25]);
const basis=registerState(2,'basis',2);
assert.deepEqual([...sampleCounts(basis,100,()=>.314)],[0,0,100,0]);
const correlated=registerState(2,'correlated',0),uniform=registerState(2,'uniform',0);
for(const state of [correlated,uniform]) {
  near(magnitudeSquared(state[2])+magnitudeSquared(state[3]),.5);
  near(magnitudeSquared(state[1])+magnitudeSquared(state[3]),.5);
}
assert.notEqual(magnitudeSquared(correlated[1]),magnitudeSquared(uniform[1]));
const report={status:'passed',scope:'finite checks of the actual visual calculation code, with independent basis-change gates and a full mixer matrix',source_sha256:crypto.createHash('sha256').update(visualSource).digest('hex'),phaseCases,blochCases,blochPresetCases:7,globalPhaseInvariant:true,registerCases,circuitCases,presetCases:3,samplingCases:2,sharedMarginalComparison:true};
fs.writeFileSync(path.join(__dirname,'visual-audit-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
