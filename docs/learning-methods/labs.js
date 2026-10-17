(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];

  // Tables and wide equations scroll locally, never the entire reading page.
  $$('main table').forEach(table => {
    if (table.parentElement.classList.contains('table-scroll')) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'table-scroll';
    wrapper.tabIndex = 0;
    wrapper.setAttribute('aria-label', 'Scrollable reference table');
    table.before(wrapper);
    wrapper.append(table);
  });

  const nav = $('#contents');
  const toggle = $('#menu-toggle');
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  const closeNav = () => {
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  };
  $$('#contents a').forEach(a => a.addEventListener('click', closeNav));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeNav(); toggle.focus(); }
  });
  document.addEventListener('click', e => {
    if (nav.classList.contains('open') && !nav.contains(e.target) && !toggle.contains(e.target)) closeNav();
  });
  const headings = $$('.chapter > h2');
  const links = $$('.contents nav a');
  let scrollPending = false;
  let lastActive = '';
  function updateReadingPosition() {
    const total = document.documentElement.scrollHeight - innerHeight;
    $('#progress-fill').style.width = `${total > 0 ? Math.min(100, scrollY / total * 100) : 0}%`;
    let active = headings[0];
    for (const heading of headings) if (heading.getBoundingClientRect().top < 165) active = heading;
    links.forEach(a => {
      const selected = a.getAttribute('href') === `#${active.id}`;
      a.classList.toggle('active', selected);
      if (selected) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
    });
    if (active.id !== lastActive) {
      const selected = links.find(a => a.getAttribute('href') === `#${active.id}`);
      if (selected) {
        const top = selected.offsetTop, bottom = top + selected.offsetHeight;
        if (top < nav.scrollTop + 30) nav.scrollTop = Math.max(0,top - 30);
        else if (bottom > nav.scrollTop + nav.clientHeight - 30) nav.scrollTop = bottom - nav.clientHeight + 30;
      }
      lastActive = active.id;
    }
    scrollPending = false;
  }
  addEventListener('scroll', () => {
    if (!scrollPending) { scrollPending = true; requestAnimationFrame(updateReadingPosition); }
  }, { passive: true });
  addEventListener('resize', updateReadingPosition);

  let closedBeforePrint = [];
  addEventListener('beforeprint', () => {
    closedBeforePrint = $$('details:not([open])');
    closedBeforePrint.forEach(d => d.open = true);
  });
  addEventListener('afterprint', () => closedBeforePrint.forEach(d => d.open = false));
  $('#solutions-toggle').addEventListener('click', e => {
    const show = e.currentTarget.getAttribute('aria-expanded') !== 'true';
    $$('details.solution').forEach(d => d.open = show);
    e.currentTarget.setAttribute('aria-expanded', String(show));
    e.currentTarget.textContent = show ? 'Hide all solutions' : 'Show all solutions';
  });

  const encoding = $('#encoding-lab');
  let K = 4, rank = 2, ys = [1,1,0];
  encoding.innerHTML = `<div class="lab-kicker">LAB 01 / GENERAL ENCODINGS</div><h3>One choice. Three representations.</h3>
    <p>Change the number of alternatives, then compare the same choice in all three encodings. The separate threshold inspector below can test a different or invalid word; the comparison stays at your selected rank.</p>
    <div class="lab-controls"><label>Alternatives K <select id="choice-count" aria-label="Number of alternatives">${Array.from({length:8},(_,i)=>`<option ${i===3?'selected':''}>${i+1}</option>`).join('')}</select></label><label>Choice rank r <select id="choice-rank" aria-label="Selected choice rank"></select></label><button type="button" id="show-invalid">Make an invalid wall</button></div>
    <div id="encoding-representations"></div><p class="lab-note">Code strings are written in the displayed index order. Binary positional digits are most significant first. ∅ means no bits are needed for a fixed choice.</p>
    <p><b>Domain-wall bits to inspect</b></p><div id="threshold-bits" class="threshold-inputs"></div><div id="wall-result" aria-live="polite"></div>`;
  function updateThresholdResult() {
    const boundary = [1,...ys,0];
    const indicators = Array.from({length:K},(_,r)=>boundary[r]-boundary[r+1]);
    const rises = ys.slice(1).reduce((s,y,i)=>s+(1-ys[i])*y,0);
    const valid = rises === 0;
    $('#wall-result').innerHTML = `<p>Inspected word: <code>${ys.join('') || '∅'}</code></p><div class="lab-status" data-valid="${valid}">${valid ? `Encoding-valid: rank ${ys.reduce((s,y)=>s+y,0)}.` : 'Invalid encoding: a 0→1 transition creates a negative indicator.'}</div><p>Indicators χ = (${indicators.join(', ')}). Their sum is ${indicators.reduce((s,v)=>s+v,0)}. Wall violations = ${rises}.</p>`;
  }
  function renderEncoding() {
    const b = Math.ceil(Math.log2(K));
    const onehot = Array.from({length:K},(_,i)=>Number(i===rank)).join('');
    const wall = Array.from({length:K-1},(_,i)=>Number(rank>=i+1)).join('') || '∅';
    const binary = b ? rank.toString(2).padStart(b,'0') : '∅';
    $('#choice-rank').innerHTML = Array.from({length:K},(_,i)=>`<option ${i===rank?'selected':''}>${i}</option>`).join('');
    $('#encoding-representations').innerHTML = `
      <div class="encoding-row"><b>One-hot</b><div><code>${onehot}</code><br>${K} bits · ${K} valid of ${2**K} words · linear indicators</div></div>
      <div class="encoding-row"><b>Domain wall</b><div><code>${wall}</code><br>${K-1} bits · ${K} valid of ${2**(K-1)} words · affine indicators</div></div>
      <div class="encoding-row"><b>Binary</b><div><code>${binary}</code><br>${b} bits · ${K} valid of ${2**b} words · indicator degree up to ${b}</div></div>`;
    $('#threshold-bits').innerHTML = ys.map((y,i)=>`<label><input type="checkbox" data-wall="${i}" ${y?'checked':''}>y${i+1}</label>`).join('') || '<span>Fixed choice: boundary indicators suffice.</span>';
    $('#show-invalid').disabled = K < 3;
    updateThresholdResult();
  }
  $('#choice-count').addEventListener('change', e => {
    K = Number(e.target.value); rank = Math.min(rank,K-1);
    ys = Array.from({length:K-1},(_,i)=>Number(rank>=i+1)); renderEncoding();
  });
  $('#choice-rank').addEventListener('change', e => {
    rank = Number(e.target.value); ys = Array.from({length:K-1},(_,i)=>Number(rank>=i+1)); renderEncoding();
  });
  $('#threshold-bits').addEventListener('change', e => {
    if (!e.target.matches('[data-wall]')) return;
    ys[Number(e.target.dataset.wall)] = Number(e.target.checked);
    updateThresholdResult();
  });
  $('#show-invalid').addEventListener('click', () => {
    ys = Array.from({length:K-1},(_,i)=>Number(i===1)); renderEncoding();
  });
  renderEncoding();

  const phase = $('#phase-lab');
  phase.innerHTML = `<div class="lab-kicker">LAB 02 / PHASE → INTERFERENCE → PROBABILITY</div><h3>Watch a mixer turn phase into probability.</h3><p>Invented one-bit energy E(x)=x. One layer, an ideal statevector, and no training. The target is x=0.</p>
    <label class="angle-control"><span><b>Cost angle γ</b><output id="gamma-value"></output></span><input id="gamma-angle" aria-label="Cost angle gamma in radians" type="range" min="-3.141592653589793" max="3.141592653589793" step="any" value="1.5707963267948966"></label>
    <label class="angle-control"><span><b>Mixer angle β</b><output id="beta-value"></output></span><input id="beta-angle" aria-label="Mixer angle beta in radians" type="range" min="-1.5707963267948966" max="1.5707963267948966" step="any" value="0"></label>
    <div class="lab-controls"><button type="button" id="phase-only">Cost layer only</button><button type="button" id="good-interference">Angles giving x=0</button><button type="button" id="bad-interference">Reverse mixer sign</button></div>
    <div class="lab-results" aria-live="polite"><div><span class="value" id="before-probability">50.0%</span><small>P(0), after cost</small></div><div><span class="value" id="after-probability"></span><small>P(0), after mixer</small></div><div><span class="value" id="expected-energy"></span><small>Expected E = P(1)</small></div></div><div class="probability-track" role="img" id="probability-bar"><span></span></div><p class="lab-note">The cost layer alone always leaves 50/50 measurement probabilities here. This exact one-bit illustration explains the mechanism; it is not a scheduling performance result.</p>`;
  function updatePhase() {
    const gamma = Number($('#gamma-angle').value), beta = Number($('#beta-angle').value);
    const p0 = Math.max(0,Math.min(1,(1-Math.sin(2*beta)*Math.sin(gamma))/2));
    $('#gamma-value').textContent = `${(gamma/Math.PI).toFixed(3)}π rad`;
    $('#beta-value').textContent = `${(beta/Math.PI).toFixed(3)}π rad`;
    $('#after-probability').textContent = `${(p0*100).toFixed(1)}%`;
    $('#expected-energy').textContent = (1-p0).toFixed(3);
    $('#probability-bar span').style.width = `${p0*100}%`;
    $('#probability-bar').setAttribute('aria-label', `Probability of zero after the mixer: ${(p0*100).toFixed(1)} percent`);
  }
  function setAngles(g,b) { $('#gamma-angle').value = g; $('#beta-angle').value = b; updatePhase(); }
  $('#gamma-angle').addEventListener('input', updatePhase);
  $('#beta-angle').addEventListener('input', updatePhase);
  $('#phase-only').addEventListener('click', () => setAngles(Math.PI/2,0));
  $('#good-interference').addEventListener('click', () => setAngles(Math.PI/2,-Math.PI/4));
  $('#bad-interference').addEventListener('click', () => setAngles(Math.PI/2,Math.PI/4));
  updatePhase();

  const lab = $('#schedule-lab');
  const vars = [
    {name:'Z1·T',start:0,p:2,m:'T'}, {name:'Z1·T',start:1,p:2,m:'T'},
    {name:'Z1·F',start:2,p:1,m:'F'}, {name:'Z1·F',start:3,p:1,m:'F'},
    {name:'Z2·T',start:0,p:1,m:'T'}, {name:'Z2·T',start:1,p:1,m:'T'},
    {name:'Z2·F',start:1,p:2,m:'F'}, {name:'Z2·F',start:2,p:2,m:'F'}
  ];
  const groups = [[0,1],[2,3],[4,5],[6,7]];
  const capacity = [[0,4],[0,5],[1,5],[2,6],[2,7],[3,7]];
  const precedence = [[1,2],[5,6]];
  const pairWeights = [...groups.map(g=>[...g,2]),...capacity.map(g=>[...g,1]),...precedence.map(g=>[...g,1])];
  let bits = Array(8).fill(0);
  lab.innerHTML = `<div class="lab-kicker">LAB 03 / THE SUPPLIED INSTANCE A · H = 4</div><h3>Connect the bits, energy and schedule.</h3><p>Toggle any start bits, including invalid combinations. The polynomial, matrix and violation list use the same bit order as the derivation above.</p><div class="lab-controls"><button type="button" data-preset="zero">Clear bits</button><button type="button" data-preset="optimal">Feasible schedule</button><button type="button" data-preset="clash">Two machine clashes</button><button type="button" data-preset="all">All bits on</button></div>
    <div class="bit-groups">${groups.map((g,k)=>`<div class="bit-group"><b>${vars[g[0]].name} · choose one start</b>${g.map(i=>`<label><input type="checkbox" data-bit="${i}" aria-label="x${i+1}: ${vars[i].name} starts at ${vars[i].start}">x${i+1}: start ${vars[i].start} → finish ${vars[i].start+vars[i].p}</label>`).join('')}</div>`).join('')}</div>
    <div class="lab-results" aria-live="polite"><div><span class="value" id="total-energy"></span><small>Complete E₄</small></div><div><span class="value" id="once-energy"></span><small>Exactly-once part</small></div><div><span class="value" id="capacity-energy"></span><small>Machine part</small></div><div><span class="value" id="precedence-energy"></span><small>Precedence part</small></div></div>
    <div id="schedule-status" class="lab-status" aria-live="polite"></div><p id="bit-vector"></p><div id="schedule-timeline"></div><div class="lab-columns"><div><b>Nonzero violations</b><ul id="violations"></ul><p id="matrix-check"></p></div><div><b>Q · highlighted intersections contribute</b><div class="matrix-wrap" tabindex="0" aria-label="Scrollable QUBO matrix"><table class="matrix-grid" id="interactive-matrix"></table></div></div></div><p class="lab-note">The energy includes offset +4. Negative diagonal terms are normal: the original nonnegative squares guarantee that the complete feasibility energy is nonnegative. The timeline displays every selected interval, even if an operation is selected more than once.</p>`;
  function timeline(active) {
    const selected = active.map(i=>({...vars[i],i})).sort((a,b)=>(a.m==='T'?0:1)-(b.m==='T'?0:1)||a.i-b.i);
    const width = 570, left = 98, scale = 105, height = 40+Math.max(1,selected.length)*29;
    let svg = `<svg class="timeline" viewBox="0 0 ${width} ${height}" role="img" aria-label="Selected processing intervals on machines T and F"><title>Selected intervals, one row per selected bit</title>`;
    for (let t=0;t<=4;t++) svg += `<line x1="${left+t*scale}" x2="${left+t*scale}" y1="22" y2="${height-8}" stroke="#d2dacd"/><text x="${left+t*scale}" y="13" text-anchor="middle">${t}</text>`;
    if (!selected.length) svg += '<text x="98" y="43">No selected intervals.</text>';
    selected.forEach((v,k)=>{
      const y = 27+k*29;
      const bad = [...capacity,...precedence].some(([i,j])=>bits[i]&&bits[j]&&(v.i===i||v.i===j));
      svg += `<text x="0" y="${y+15}">x${v.i+1} · ${v.name}</text><rect x="${left+v.start*scale}" y="${y}" width="${v.p*scale}" height="21" rx="2" fill="${v.name.startsWith('Z1')?'#2d7567':'#91ad97'}" ${bad?'stroke="#8d3925" stroke-width="2"':''}/><text x="${left+v.start*scale+v.p*scale/2}" y="${y+15}" text-anchor="middle" style="fill:${v.name.startsWith('Z1')?'#fff':'#173b2f'}">[${v.start},${v.start+v.p})</text>`;
    });
    return svg+'</svg>';
  }
  function updateSchedule() {
    $$('.bit-groups input',lab).forEach(input=>input.checked=Boolean(bits[Number(input.dataset.bit)]));
    const counts = groups.map(g=>g.reduce((s,i)=>s+bits[i],0));
    const once = counts.reduce((s,c)=>s+(c-1)**2,0);
    const capHits = capacity.filter(([i,j])=>bits[i]&&bits[j]);
    const precHits = precedence.filter(([i,j])=>bits[i]&&bits[j]);
    const total = once+capHits.length+precHits.length;
    $('#total-energy').textContent = total;
    $('#once-energy').textContent = once;
    $('#capacity-energy').textContent = capHits.length;
    $('#precedence-energy').textContent = precHits.length;
    const encodingValid = counts.every(c=>c===1);
    const status = $('#schedule-status');
    status.dataset.valid = String(total===0);
    status.textContent = total===0 ? 'Feasible schedule. Makespan = 4, the proved optimum.' : encodingValid ? 'Encoding-valid, but scheduling constraints are violated.' : 'Not a valid one-hot encoding: some operations have zero or multiple starts.';
    $('#bit-vector').textContent = `x = (${bits.join(', ')})`;
    const list = [];
    counts.forEach((c,k)=>{if(c!==1) list.push(`${vars[groups[k][0]].name}: ${c} starts → (${c}−1)² = ${(c-1)**2}`);});
    capHits.forEach(([i,j])=>list.push(`Machine ${vars[i].m}: x${i+1}x${j+1} = 1`));
    precHits.forEach(([i,j])=>list.push(`Job precedence: x${i+1}x${j+1} = 1`));
    $('#violations').innerHTML = list.length ? list.map(s=>`<li>${s}</li>`).join('') : '<li>None. All constraints hold.</li>';
    const active = bits.map((b,i)=>b?i:-1).filter(i=>i>=0);
    const pairTotal = pairWeights.reduce((s,[i,j,w])=>s+w*bits[i]*bits[j],0);
    $('#matrix-check').textContent = `Matrix check: ${-active.length} (diagonal) + ${pairTotal} (pairs) + 4 (offset) = ${total}.`;
    let matrix = '<thead><tr><th scope="col">Q</th>'+bits.map((b,i)=>`<th scope="col" class="${b?'selected':''}">x${i+1}</th>`).join('')+'</tr></thead><tbody>';
    for(let i=0;i<8;i++) {
      matrix += `<tr><th scope="row" class="${bits[i]?'selected':''}">x${i+1}</th>`;
      for(let j=0;j<8;j++) {
        const q = i===j ? -1 : pairWeights.find(([a,b])=>a===i&&b===j)?.[2] || 0;
        matrix += `<td class="${bits[i]&&bits[j]?'hit ':''}${q===0?'zero':''}">${q || '·'}</td>`;
      }
      matrix += '</tr>';
    }
    $('#interactive-matrix').innerHTML = matrix+'</tbody>';
    $('#schedule-timeline').innerHTML = timeline(active);
    // A cross-check within the demo catches accidental divergence of its two displays.
    if (-active.length+pairTotal+4 !== total) throw new Error('Interactive energy mismatch');
  }
  $('.bit-groups',lab).addEventListener('change', e=> {
    if (!e.target.matches('[data-bit]')) return;
    bits[Number(e.target.dataset.bit)] = Number(e.target.checked); updateSchedule();
  });
  $$('[data-preset]',lab).forEach(button=>button.addEventListener('click',()=>{
    const presets = {zero:[0,0,0,0,0,0,0,0],optimal:[0,1,0,1,1,0,1,0],clash:[1,0,1,0,1,0,1,0],all:[1,1,1,1,1,1,1,1]};
    bits = [...presets[button.dataset.preset]]; updateSchedule();
  }));
  updateSchedule();

  const audit = JSON.parse($('#audit-data').textContent);
  const summary = document.createElement('p');
  summary.className = 'audit-status';
  summary.textContent = `Local mathematical audit: ${audit.checks.length} check groups passed. Finite checks support the worked examples; the general guarantees are proved in the text.`;
  $('#sources').after(summary);
  updateReadingPosition();
})();
