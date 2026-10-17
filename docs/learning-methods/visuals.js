/* Local, ideal calculations for the guide's conceptual visualisations. */
(() => {
  'use strict';
  const complex = (re, im = 0) => ({re, im});
  const multiply = (a,b) => complex(a.re*b.re-a.im*b.im,a.re*b.im+a.im*b.re);
  const add = (a,b) => complex(a.re+b.re,a.im+b.im);
  const scale = (a,k) => complex(a.re*k,a.im*k);
  const magnitudeSquared = z => z.re*z.re+z.im*z.im;
  const energies = [1,-1,4,6];
  function phaseState(probabilityZero, degrees) {
    const angle = degrees*Math.PI/180;
    const radius = Math.sqrt(1-probabilityZero);
    return [complex(Math.sqrt(probabilityZero)),complex(radius*Math.cos(angle),radius*Math.sin(angle))];
  }
  function blochState(thetaDegrees, phiDegrees, globalPhase = false) {
    const theta=thetaDegrees*Math.PI/180,phi=phiDegrees*Math.PI/180;
    let state=[complex(Math.cos(theta/2)),complex(Math.sin(theta/2)*Math.cos(phi),Math.sin(theta/2)*Math.sin(phi))];
    if(globalPhase) state=state.map(z=>multiply(z,complex(0,1)));
    const [a,b]=state;
    const r=[2*(a.re*b.re+a.im*b.im),2*(a.re*b.im-a.im*b.re),magnitudeSquared(a)-magnitudeSquared(b)];
    return {state,r,plus:r.map(value=>(1+value)/2)};
  }
  function registerState(n, mode, selected) {
    const size = 2**n;
    const state = Array.from({length:size},()=>complex(0));
    if (mode==='basis') state[selected]=complex(1);
    else if (mode==='uniform') state.forEach((_,i)=>state[i]=complex(1/Math.sqrt(size)));
    else if (mode==='correlated') { state[0]=complex(Math.SQRT1_2); state[size-1]=complex(Math.SQRT1_2); }
    else { state[n===1?0:1]=complex(Math.sqrt(3)/2); state[n===1?1:size-2]=complex(.5); }
    return state;
  }
  function qaoaState(gamma, beta, stage) {
    let state = energies.map(()=>complex(.5));
    if (stage>=1) state=state.map((a,i)=>multiply(a,complex(Math.cos(gamma*energies[i]),-Math.sin(gamma*energies[i]))));
    if (stage>=2) {
      for (const bit of [1,0]) {
        const previous=state;
        state=previous.map((a,i)=>add(scale(a,Math.cos(beta)),multiply(complex(0,-Math.sin(beta)),previous[i^(1<<bit)])));
      }
    }
    return state;
  }
  function sampleCounts(state,count,random=Math.random) {
    const probabilities=state.map(magnitudeSquared), counts=state.map(()=>0);
    for(let shot=0;shot<count;shot++) {
      const r=random(); let cumulative=0, choice=state.length-1;
      for(let i=0;i<state.length;i++) { cumulative+=probabilities[i]; if(r<cumulative) {choice=i;break;} }
      counts[choice]++;
    }
    return counts;
  }
  // The same pure calculations can be checked without a browser or remote QPU.
  if(typeof module!=='undefined' && module.exports) module.exports={phaseState,blochState,registerState,qaoaState,sampleCounts,magnitudeSquared,energies};
  if(typeof document==='undefined') return;

  const clean = x => Math.abs(x)<5e-10?0:x;
  const fixed = x => clean(x).toFixed(3).replace(/\.000$/,'');
  const formatComplex = z => {
    const re=clean(z.re),im=clean(z.im);
    if(!im) return fixed(re);
    if(!re) return fixed(im)+'i';
    return fixed(re)+(im<0?' − ':' + ')+fixed(Math.abs(im))+'i';
  };
  const percent = p => (100*p).toFixed(1).replace(/\.0$/,'')+'%';
  const label = (i,n) => i.toString(2).padStart(n,'0');
  const find = (root,id) => root.querySelector('#'+id);
  function arrow(z,id,description,mini=false) {
    const x=110+68*z.re,y=100-68*z.im;
    return `<svg class="amplitude-plane ${mini?'amplitude-plane-small':''}" viewBox="0 0 220 200" role="img" aria-label="${description}">
      <defs><marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent)"/></marker></defs>
      <circle cx="110" cy="100" r="68" fill="none" stroke="var(--line)" stroke-width="1"/>
      <path d="M 28 100 H 192 M 110 18 V 182" fill="none" stroke="var(--line)" stroke-width="1"/>
      ${!mini?'<text x="215" y="119" text-anchor="end">+real</text><text x="110" y="12" text-anchor="middle">+imaginary</text><text x="110" y="193" text-anchor="middle">−imaginary</text><text x="5" y="119">−real</text>':''}
      ${magnitudeSquared(z)>1e-14?`<path d="M 110 100 L ${x} ${y}" fill="none" stroke="var(--accent)" stroke-width="3" marker-end="url(#${id})"/>`:'<circle cx="110" cy="100" r="3" fill="var(--accent)"/>'}
      <circle cx="110" cy="100" r="2" fill="var(--muted)"/>
    </svg>`;
  }
  function probabilityBar(value) {
    return `<div class="concept-probability"><span style="width:${Math.max(0,Math.min(1,value))*100}%"></span></div>`;
  }

  const phaseRoot=document.getElementById('amplitude-arrow-lab');
  if(phaseRoot) {
    phaseRoot.innerHTML=`<div class="lab-kicker">VISUAL / AMPLITUDE AND PROBABILITY</div><h3>Rotate an amplitude; watch what stays unchanged</h3>
      <p>This is a chosen family of ideal one-qubit states, not a scheduling instance. We choose the amplitude for 0 to point along the positive real axis. The second arrow's angle is its phase relative to the first.</p>
      <div class="concept-controls"><label for="av-probability">Choose probability of outcome 0: <output id="av-probability-value"></output><input id="av-probability" type="range" min="0" max="100" value="50" step="1"></label><label for="av-phase">Relative phase of amplitude for 1: <output id="av-phase-value"></output><input id="av-phase" type="range" min="0" max="360" value="45" step="1"></label></div>
      <div id="av-panels" class="amplitude-panels"></div><p id="av-explanation" aria-live="polite"></p>
      <p class="lab-note">The circle marks amplitude length 1. Each arrow lives in a mathematical complex plane, not physical space and not a Bloch sphere. If one amplitude is zero, its direction and the relative phase have no observable effect here. These sliders choose a state for inspection; an actual circuit prepares states using gates.</p>`;
    function renderPhase() {
      const p=Number(find(phaseRoot,'av-probability').value)/100, degrees=Number(find(phaseRoot,'av-phase').value);
      const state=phaseState(p,degrees);
      find(phaseRoot,'av-probability-value').textContent=percent(p);
      find(phaseRoot,'av-phase-value').textContent=degrees+'° = '+fixed(degrees/180)+'π radians';
      find(phaseRoot,'av-panels').innerHTML=state.map((z,i)=>`<div><h4>Amplitude for outcome ${i}</h4>${arrow(z,'av-arrow-'+i,'Amplitude for outcome '+i+': '+formatComplex(z))}<div class="concept-number">α${i} = ${formatComplex(z)}</div><p class="concept-small">Length = ${fixed(Math.sqrt(magnitudeSquared(z)))}</p><b>Probability = length² = ${percent(magnitudeSquared(z))}</b>${probabilityBar(magnitudeSquared(z))}</div>`).join('');
      find(phaseRoot,'av-explanation').textContent='Changing only the phase rotates the second arrow without changing either probability. Here the probabilities add to '+percent(state.reduce((s,z)=>s+magnitudeSquared(z),0))+'. Change the probability slider to change the lengths instead.';
    }
    find(phaseRoot,'av-probability').addEventListener('input',renderPhase);
    find(phaseRoot,'av-phase').addEventListener('input',renderPhase);
    renderPhase();
  }

  const blochRoot=document.getElementById('bloch-sphere-lab');
  if(blochRoot) {
    blochRoot.innerHTML=`<div class="lab-kicker">VISUAL / ONE QUBIT, TWO CONNECTED PICTURES</div><h3>Complex arrows describe coefficients. The sphere describes the whole state.</h3>
      <p>Start with α₀ = 1/√2 and α₁ = (1 + i)/2. The second amplitude has real and imaginary parts. Move around the sphere to see why direction matters even when the usual 0/1 probabilities stay unchanged.</p>
      <div class="concept-controls"><label for="bv-theta">Tilt from the north pole θ: <output id="bv-theta-value"></output><input type="range" id="bv-theta" min="0" max="180" value="90" step="1"></label><label for="bv-phi">Relative phase around the axis φ: <output id="bv-phi-value"></output><input type="range" id="bv-phi" min="0" max="360" value="45" step="1"></label></div>
      <div class="lab-controls"><button type="button" data-bloch="90,45">Complex example</button><button type="button" data-bloch="90,90">+i state</button><button type="button" data-bloch="90,0">Real + state</button><button type="button" data-bloch="90,180">Real − state</button><button type="button" data-bloch="0,0">Definite 0</button><button type="button" data-bloch="180,0">Definite 1</button></div>
      <label class="bloch-gauge"><input id="bv-global" type="checkbox"> Multiply both amplitudes by i: change only global phase</label>
      <div class="bloch-layout"><div><div id="bv-sphere"></div><button type="button" id="bv-view">Turn the drawing's viewpoint</button><p class="lab-note">The highlighted radius represents one whole pure state. Dashed portions of the grid lie behind the sphere. Turning the viewpoint changes the drawing, not the state.</p></div><div id="bv-arrows" class="bloch-arrows"></div></div>
      <p id="bv-state" class="concept-number"></p><p id="bv-explanation" aria-live="polite"></p>
      <h4>Different measurement settings reveal different information</h4><p>Each row is a separate experiment on freshly prepared copies. Within a row, the two probabilities add to 100%. We do not measure all three settings at once.</p>
      <div id="bv-measurements" class="bloch-measurements"></div><p id="bv-coordinates" class="lab-note"></p>
      <p class="lab-note">This sphere represents one pure qubit, not the full joint state of many entangled qubits. Its axes are mathematical measurement settings. The point is not the qubit's location in the room. Displayed decimals are rounded.</p>`;
    let azimuth=45;
    function sphereSvg(r,thetaDegrees,phiDegrees) {
      const width=Math.max(210,Math.min(430,Math.round(find(blochRoot,'bv-sphere').getBoundingClientRect().width))),height=300;
      const radius=Math.min(100,width*.29),cx=width/2,cy=150;
      const a=azimuth*Math.PI/180,e=24*Math.PI/180;
      const right=[-Math.sin(a),Math.cos(a),0],up=[-Math.cos(a)*Math.sin(e),-Math.sin(a)*Math.sin(e),Math.cos(e)],towards=[Math.cos(a)*Math.cos(e),Math.sin(a)*Math.cos(e),Math.sin(e)];
      const dot=(p,q)=>p.reduce((s,v,i)=>s+v*q[i],0);
      const project=p=>[cx+radius*dot(p,right),cy-radius*dot(p,up)];
      const path=(fn,accent=false)=>Array.from({length:96},(_,i)=>{
        const p=fn(i*Math.PI/48),q=fn((i+1)*Math.PI/48),v=project(p),w=project(q),back=dot(p,towards)<0;
        return `<path d="M ${v.join(' ')} L ${w.join(' ')}" fill="none" stroke="${accent?'var(--accent)':'var(--muted)'}" stroke-opacity="${accent?.55:back?.2:.38}" ${back?'stroke-dasharray="2 3"':''}/>`;
      }).join('');
      const grid=[path(t=>[Math.cos(t),Math.sin(t),0]),path(t=>[Math.cos(t),0,Math.sin(t)]),path(t=>[0,Math.cos(t),Math.sin(t)])].join('');
      const theta=thetaDegrees*Math.PI/180,phi=phiDegrees*Math.PI/180;
      const latitude=path(t=>[Math.sin(theta)*Math.cos(t),Math.sin(theta)*Math.sin(t),Math.cos(theta)],true);
      const meridian=path(t=>[Math.sin(t)*Math.cos(phi),Math.sin(t)*Math.sin(phi),Math.cos(t)],true);
      const statePoint=project(r),north=project([0,0,1]),south=project([0,0,-1]);
      const axes=[[1,0,0],[0,1,0]].map((p,i)=>{const end=project(p),side=end[0]<cx?-1:1;return `<path d="M ${cx} ${cy} L ${end.join(' ')}" stroke="var(--muted)" stroke-width="1.1"/><text x="${end[0]+side*8}" y="${end[1]+4}" text-anchor="${side<0?'end':'start'}">${i?'Y+':'X+'}</text>`;}).join('');
      return `<svg class="bloch-sphere" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="Bloch sphere. State coordinates X ${fixed(r[0])}, Y ${fixed(r[1])}, Z ${fixed(r[2])}. North is definite 0, south definite 1."><defs><marker id="bv-tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent)"/></marker></defs><circle cx="${cx}" cy="${cy}" r="${radius}" fill="none" stroke="var(--line)"/>${grid}${latitude}${meridian}<path d="M ${north.join(' ')} L ${south.join(' ')}" stroke="var(--muted)"/>${axes}<text x="${north[0]}" y="${north[1]-20}" text-anchor="middle">|0⟩ · Z = +1</text><text x="${south[0]}" y="${south[1]+26}" text-anchor="middle">|1⟩ · Z = −1</text><path d="M ${cx} ${cy} L ${statePoint.join(' ')}" stroke="var(--accent)" stroke-width="3" marker-end="url(#bv-tip)" ${dot(r,towards)<0?'stroke-dasharray="5 3"':''}/><circle cx="${statePoint[0]}" cy="${statePoint[1]}" r="5" fill="var(--accent)"/><circle cx="${cx}" cy="${cy}" r="2.5" fill="var(--muted)"/></svg>`;
    }
    function renderBloch() {
      const theta=Number(find(blochRoot,'bv-theta').value),phi=Number(find(blochRoot,'bv-phi').value),global=find(blochRoot,'bv-global').checked;
      const {state,r,plus}=blochState(theta,phi,global);
      find(blochRoot,'bv-theta-value').textContent=theta+'°';find(blochRoot,'bv-phi-value').textContent=phi+'°';
      find(blochRoot,'bv-sphere').innerHTML=sphereSvg(r,theta,phi);
      find(blochRoot,'bv-arrows').innerHTML=state.map((z,i)=>`<div><b>α${i} = ${formatComplex(z)}</b>${arrow(z,'bv-amplitude-'+i,'Complex amplitude '+i+': '+formatComplex(z))}<span>Usual readout ${i}: ${percent(magnitudeSquared(z))}</span></div>`).join('');
      find(blochRoot,'bv-state').textContent='|ψ⟩ = ('+formatComplex(state[0])+') |0⟩ + ('+formatComplex(state[1])+') |1⟩';
      find(blochRoot,'bv-explanation').textContent=(theta===0||theta===180?'At a pole, changing φ has no observable effect: one amplitude is zero. ':'Change φ at fixed θ: the point goes around a latitude, and ordinary Z readout probabilities stay fixed. X or Y readout can still change. ')+(global?'Both amplitude arrows have been rotated by 90°. The Bloch point and every measurement probability are unchanged: that is global phase.':'The first amplitude is chosen real and nonnegative; the second arrow shows their relative phase.');
      find(blochRoot,'bv-measurements').innerHTML=[plus[2],plus[0],plus[1]].map((p,i)=>`<div class="bloch-measurement"><b>${['Z · usual readout','X · add Hadamard','Y · phase −i, then Hadamard'][i]}</b><span>${i?'Outcome +1':'Read 0 (+1)'}: ${percent(p)}</span>${probabilityBar(p)}<span>${i?'Outcome −1':'Read 1 (−1)'}: ${percent(1-p)}</span></div>`).join('');
      find(blochRoot,'bv-coordinates').textContent='Sphere coordinates: rX = '+fixed(r[0])+', rY = '+fixed(r[1])+', rZ = '+fixed(r[2])+'. Each coordinate equals P(+1) − P(−1) for its setting. rZ is an average, not a new bit value.';
    }
    for(const id of ['bv-theta','bv-phi'])find(blochRoot,id).addEventListener('input',renderBloch);
    find(blochRoot,'bv-global').addEventListener('change',renderBloch);
    blochRoot.querySelectorAll('[data-bloch]').forEach(button=>button.addEventListener('click',()=>{const [theta,phi]=button.dataset.bloch.split(',');find(blochRoot,'bv-theta').value=theta;find(blochRoot,'bv-phi').value=phi;find(blochRoot,'bv-global').checked=false;renderBloch();}));
    find(blochRoot,'bv-view').addEventListener('click',()=>{azimuth=(azimuth+90)%360;renderBloch();});
    if(typeof ResizeObserver!=='undefined')new ResizeObserver(renderBloch).observe(find(blochRoot,'bv-sphere'));
    renderBloch();
  }

  const registerRoot=document.getElementById('register-explorer-lab');
  if(registerRoot) {
    registerRoot.innerHTML=`<div class="lab-kicker">VISUAL / BASIS LABELS AND WHOLE-REGISTER STATES</div><h3>One coordinate for each complete bitstring</h3>
      <p>Choose a register size and a state. Click an outcome label to inspect its basis vector. The selected basis vector and the whole state vector are different objects. Coordinates read left to right, continuing on the next row when they wrap.</p>
      <div class="lab-controls"><label>Qubits N <select id="rv-size" aria-label="Register size"><option>1</option><option selected>2</option><option>3</option><option>4</option></select></label><label>Whole state <select id="rv-mode" aria-label="Register state"><option value="weighted" selected>Two outcomes: 75% / 25%</option><option value="uniform">Equal superposition</option><option value="basis">Selected basis state</option><option value="correlated">Only all-zero / all-one</option></select></label></div>
      <p id="rv-dimension"></p><p id="rv-selection-note" class="lab-note"></p><div id="rv-outcomes" class="register-labels" role="group" aria-label="Outcome label to inspect"></div>
      <div class="coordinate-block"><b id="rv-basis-title"></b><div id="rv-basis-vector" class="coordinate-vector"></div></div>
      <div class="coordinate-block"><b>Whole state |ψ⟩: amplitudes, in that same order</b><div id="rv-whole-vector" class="coordinate-vector"></div></div>
      <div id="rv-probabilities" class="register-probabilities"></div><p id="rv-result" aria-live="polite"></p><p id="rv-marginals" class="lab-note"></p>
      <p class="lab-note">These are illustrative ideal pure states. Bars show probabilities calculated from their amplitudes, not measured hardware data. With two or more qubits, the all-zero/all-one state and equal superposition have identical individual-qubit probabilities while different joint outcomes occur; a joint histogram alone does not establish entanglement.</p>`;
    let selected=1;
    function renderRegister() {
      const n=Number(find(registerRoot,'rv-size').value),size=2**n,mode=find(registerRoot,'rv-mode').value;
      selected=Math.min(selected,size-1);
      const state=registerState(n,mode,selected), probabilities=state.map(magnitudeSquared);
      find(registerRoot,'rv-selection-note').textContent=mode==='basis'?'In selected-basis-state mode, clicking an outcome also chooses the whole state.':'In this mode, clicking an outcome only highlights its coordinate; the whole example state stays fixed.';
      find(registerRoot,'rv-dimension').textContent=n+' qubit'+(n===1?'':'s')+' → '+size+' complete bitstring outcomes → '+size+' amplitude coordinates.';
      find(registerRoot,'rv-outcomes').innerHTML=state.map((_,i)=>`<button type="button" data-basis="${i}" aria-pressed="${i===selected}">|${label(i,n)}⟩</button>`).join('');
      find(registerRoot,'rv-basis-title').textContent='Selected basis vector |'+label(selected,n)+'⟩: one 1 marks its coordinate';
      const coordinates=values=>values.map((value,i)=>`<div class="coordinate" ${i===selected?'data-selected="true"':''}><span>${label(i,n)}</span><b>${value}</b></div>`).join('');
      find(registerRoot,'rv-basis-vector').innerHTML=coordinates(state.map((_,i)=>i===selected?'1':'0'));
      find(registerRoot,'rv-whole-vector').innerHTML=coordinates(state.map((z,i)=>mode==='uniform'?'1/√'+size:mode==='correlated'&&(i===0||i===size-1)?'1/√2':mode==='weighted'&&i===(n===1?0:1)?'√3/2':formatComplex(z)));
      find(registerRoot,'rv-probabilities').innerHTML=probabilities.map((p,i)=>`<div class="register-probability-row"><code>${label(i,n)}</code>${probabilityBar(p)}<span>${percent(p)}</span></div>`).join('');
      const terms=state.map((z,i)=>magnitudeSquared(z)>1e-12?formatComplex(z)+' |'+label(i,n)+'⟩':null).filter(Boolean);
      find(registerRoot,'rv-result').textContent='Whole state, with rounded amplitudes: |ψ⟩ = '+terms.join(' + ')+'. Total probability = '+percent(probabilities.reduce((a,b)=>a+b,0))+'.';
      find(registerRoot,'rv-marginals').textContent='Individual-qubit chances of reading 1: '+Array.from({length:n},(_,bit)=>'position '+(bit+1)+': '+percent(probabilities.reduce((s,p,i)=>s+(((i>>(n-1-bit))&1)?p:0),0))).join('; ')+'. These alone do not describe the whole joint state.';
    }
    find(registerRoot,'rv-size').addEventListener('change',renderRegister);
    find(registerRoot,'rv-mode').addEventListener('change',renderRegister);
    find(registerRoot,'rv-outcomes').addEventListener('click',e=>{
      const button=e.target.closest('button[data-basis]');
      if(button) {selected=Number(button.dataset.basis);renderRegister();}
    });
    renderRegister();
  }

  const qaoaRoot=document.getElementById('qaoa-register-lab');
  if(qaoaRoot) {
    qaoaRoot.innerHTML=`<div class="lab-kicker">VISUAL / ONE EXACT TWO-QUBIT QAOA LAYER</div><h3>The costs stay fixed. The amplitudes and probabilities change.</h3>
      <p>Reuse the invented energy from chapter 02: E(x₁,x₂) = 1 + 3x₁ − 2x₂ + 4x₁x₂. The left bit is x₁. Candidate 01 has the lowest cost, −1. This is an algebra demonstration, not a scheduling benchmark or a hardware run.</p>
      <div class="lab-controls"><button type="button" id="qv-low">Angles favour low costs</button><button type="button" id="qv-high">Angles favour high costs</button><button type="button" id="qv-zero">Zero angles</button></div>
      <div class="concept-controls"><label for="qv-gamma">Cost angle γ: <output id="qv-gamma-value"></output><input type="range" id="qv-gamma" min="-64" max="64" value="-32" step="1"></label><label for="qv-beta">Mixer angle β: <output id="qv-beta-value"></output><input type="range" id="qv-beta" min="-32" max="32" value="-16" step="1"></label></div>
      <div class="lab-controls"><button type="button" id="qv-previous">Previous step</button><span id="qv-step"></span><button type="button" id="qv-next">Next step</button></div><h4 id="qv-title"></h4>
      <div class="qaoa-candidate-head concept-small"><span>Candidate and fixed cost</span><span>Complex amplitude</span><span>Probability if measured now</span></div><div id="qv-candidates"></div>
      <p id="qv-explanation" aria-live="polite"></p><p id="qv-mean" class="concept-number"></p>
      <div class="lab-controls"><button type="button" id="qv-sample">Simulate 100 fresh measurements</button></div><div id="qv-samples" aria-live="polite"><p>No measurements drawn yet. Bars above are exact ideal probabilities.</p></div>
      <p class="lab-note">Each arrow is an amplitude in its own mathematical plane; the circle means length 1. A cost step rotates arrows without changing their lengths. The X mixer can change lengths by combining amplitudes. Sliders manually choose angles here; a QAOA optimiser would propose them using cost feedback. Changing the controls clears old samples. Simulated sample counts vary between runs.</p>`;
    let stage=0,counts=null;
    const angles=()=>[Number(find(qaoaRoot,'qv-gamma').value)*Math.PI/64,Number(find(qaoaRoot,'qv-beta').value)*Math.PI/64];
    function renderQaoa() {
      const [gamma,beta]=angles(),state=qaoaState(gamma,beta,stage),probabilities=state.map(magnitudeSquared);
      find(qaoaRoot,'qv-gamma-value').textContent=fixed(gamma/Math.PI)+'π radians';
      find(qaoaRoot,'qv-beta-value').textContent=fixed(beta/Math.PI)+'π radians';
      find(qaoaRoot,'qv-step').textContent=(stage+1)+' / 3';
      find(qaoaRoot,'qv-previous').disabled=stage===0;
      find(qaoaRoot,'qv-next').disabled=stage===2;
      find(qaoaRoot,'qv-title').textContent=['1 · Prepare equal amplitudes','2 · Cost step: rotate each amplitude by −γE(x)','3 · X mixer: combine amplitudes across bit flips'][stage];
      find(qaoaRoot,'qv-candidates').innerHTML=state.map((z,i)=>`<div class="qaoa-candidate"><div><b>${label(i,2)}</b><div>Cost E = ${energies[i]}</div>${i===1?'<span class="concept-small">Lowest-cost candidate</span>':''}</div><div>${arrow(z,'qv-arrow-'+i,'Amplitude of '+label(i,2)+': '+formatComplex(z),true)}<div class="concept-number">${formatComplex(z)}</div></div><div>${probabilityBar(probabilities[i])}<b>${percent(probabilities[i])}</b></div></div>`).join('');
      find(qaoaRoot,'qv-explanation').textContent=['No candidate is preferred yet: every amplitude is 1/2, so every probability is 1/4. Changing the cost or mixer angles does not affect this preparation stage.','The costs give different phase changes. Every amplitude still has length 1/2 and every probability is still 25%. The cost step alone has not made 01 more likely.','The mixer uses sums of complex contributions. With useful angles the distribution can favour lower costs; with other angles it can favour higher costs. The fixed cost column has not changed.'][stage];
      const expected=probabilities.reduce((s,p,i)=>s+p*energies[i],0);
      find(qaoaRoot,'qv-mean').textContent='Exact mean cost of this distribution = '+fixed(expected)+'. Best possible candidate cost remains −1.';
      find(qaoaRoot,'qv-samples').innerHTML=counts?`<div class="sample-counts">${counts.map((count,i)=>`<div><b>${label(i,2)}</b><span>${count} / 100</span></div>`).join('')}</div><p>Measured sample mean = ${fixed(counts.reduce((s,count,i)=>s+count*energies[i],0)/100)}. This finite sample is not an optimality certificate.</p>`:'<p>No measurements drawn yet. Bars above are exact ideal probabilities.</p>';
    }
    const resetAndRender=()=>{counts=null;renderQaoa();};
    find(qaoaRoot,'qv-gamma').addEventListener('input',resetAndRender);
    find(qaoaRoot,'qv-beta').addEventListener('input',resetAndRender);
    find(qaoaRoot,'qv-previous').addEventListener('click',()=>{stage=Math.max(0,stage-1);resetAndRender();});
    find(qaoaRoot,'qv-next').addEventListener('click',()=>{stage=Math.min(2,stage+1);resetAndRender();});
    for(const [id,g,b] of [['qv-low',-32,-16],['qv-high',-32,16],['qv-zero',0,0]]) find(qaoaRoot,id).addEventListener('click',()=>{find(qaoaRoot,'qv-gamma').value=g;find(qaoaRoot,'qv-beta').value=b;stage=2;resetAndRender();});
    find(qaoaRoot,'qv-sample').addEventListener('click',()=>{const [g,b]=angles();counts=sampleCounts(qaoaState(g,b,stage),100);renderQaoa();});
    renderQaoa();
  }
})();
