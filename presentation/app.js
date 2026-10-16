import { slideReplay, alternativeReplay, smallReplay } from './data.js';
import { parseReplay, makespan, jobState, validateSchedule, officialScheduleToReplay } from './model.js';
import { createScene, escapeHtml as esc } from './scene.js';

const $ = id => document.getElementById(id);
const datasets = new Map([['slide', slideReplay], ['alternative', alternativeReplay], ['small', smallReplay]]);
let replay, scene, validation;
let time = 0, selected = null, playing = false, lastFrame = null;
let lastAnnouncedTime = -1;
const f = x => Number.isInteger(x) ? String(x) : x.toFixed(1);

function selectPart(job) {
  selected = selected === job ? null : job;
  update();
}

function renderTimeline(target, full = false) {
  const end = Math.max(1, makespan(replay));
  const step = Math.max(1, Math.ceil(end / 12));
  const ticks = Array.from({ length: Math.floor(end / step) + 1 }, (_, i) => i * step);
  if (ticks.at(-1) !== end) ticks.push(end);
  target.innerHTML = `<div class="timeline" style="--tick:${100 * step / end}%"><div class="timeline-axis">${ticks.map(i => `<span class="axis-tick" style="left:${i / end * 100}%">${f(i)}${full && i === end ? ' h' : ''}</span>`).join('')}</div>${replay.machines.map(m => `<div class="timeline-row"><span class="timeline-machine">${esc(m.id)}</span><div class="timeline-track">${replay.schedule.filter(o => o.machine === m.id).map(o => {
    const job = replay.jobs.find(j => j.id === o.job);
    return `<button class="operation" data-job="${esc(o.job)}" data-start="${o.start}" style="left:${o.start / end * 100}%;width:calc(${(o.end - o.start) / end * 100}% - 2px);--job-color:${job.color}" aria-label="${esc(o.job)} on ${esc(m.name)}, ${f(o.start)} to ${f(o.end)} hours" title="${esc(o.job)} · ${esc(m.name)} · ${f(o.start)}–${f(o.end)} h">${esc(o.job)}${full ? ` <span class="op-duration">/ ${f(o.end - o.start)} h</span>` : ''}</button>`;
  }).join('')}</div></div>`).join('')}<div class="timeline-cursor" aria-hidden="true"></div></div>`;
  target.querySelectorAll('.operation').forEach(button => button.addEventListener('click', () => {
    selected = button.dataset.job;
    playing = false;
    time = Number(button.dataset.start);
    update();
  }));
}

function renderEvidence() {
  const p = replay.provenance;
  $('constraint-list').innerHTML = validation.checks.map(c => `<div class="constraint ${c.issues.length ? 'failed' : ''}"><span class="constraint-mark" aria-hidden="true">${c.issues.length ? '×' : '✓'}</span><div><h3>${esc(c.label)}</h3><p>${esc(c.issues.length ? c.issues.join(' ') : c.detail)}</p></div></div>`).join('');
  $('feasibility-badge').textContent = validation.feasible ? '✓ Feasible schedule' : '× Constraint violations';
  $('feasibility-badge').classList.toggle('invalid', !validation.feasible);
  $('evidence-origin').textContent = p.kind === 'illustration' ? 'Illustration, openly labeled.' : 'Imported schedule record.';
  $('evidence-description').textContent = p.description || 'Schedule supplied in the imported replay file.';
  const fields = [['Method', p.method], ['Source', p.source || 'User supplied'], ['Backend', p.backend || 'Not applicable / not supplied'], ['Job ID', p.jobId || 'No remote run recorded']];
  $('evidence-metadata').innerHTML = fields.map(([key, value]) => `<dt>${esc(key)}</dt><dd>${esc(value)}</dd>`).join('');
  $('run-note').textContent = p.kind === 'illustration' ? 'Baseline completion is pending. This replay is not evidence of a QAOA or VeloxQ run.' : 'Feasibility is checked locally. Imported method and job metadata are self-reported; this viewer does not authenticate remote execution or prove optimality.';
}

function loadReplay(value) {
  replay = parseReplay(value);
  validation = validateSchedule(replay);
  time = 0; selected = null; playing = false; lastFrame = null; lastAnnouncedTime = -1;
  scene = createScene($('factory-scene'), replay, selectPart);
  $('time-total').textContent = f(makespan(replay));
  $('scrubber').max = makespan(replay);
  $('makespan').textContent = f(makespan(replay));
  $('job-count').textContent = replay.jobs.length;
  $('source-label').textContent = `${replay.provenance.label} · ${replay.provenance.kind === 'illustration' ? 'illustrative replay' : 'imported record'}`;
  $('factory-scene').setAttribute('aria-label', `Pixel art factory with ${replay.machines.length} processing stations`);
  $('factory-route').innerHTML = replay.machines.map(m => esc(m.name.toUpperCase())).join(' <b>→</b> ');
  $('problem-description').textContent = `${replay.jobs.length === 2 ? 'Two' : replay.jobs.length === 3 ? 'Three' : replay.jobs.length} parts. ${replay.machines.length === 2 ? 'Two' : 'Three'} machines.`;
  $('summary-provenance').textContent = replay.provenance.kind === 'illustration' ? 'Illustration only. No solver run.' : `${replay.provenance.method} · imported metadata`;
  $('mini-validation').textContent = validation.feasible ? '✓ Feasibility checked' : '× Schedule has conflicts';
  $('mini-validation').classList.toggle('invalid', !validation.feasible);
  $('part-list').innerHTML = replay.jobs.map(j => `<button class="part-button" data-part="${esc(j.id)}" style="--job-color:${j.color}" aria-pressed="false"><span class="part-dot" aria-hidden="true"></span><strong>${esc(j.id)}</strong><span class="part-state"></span></button>`).join('');
  $('part-list').querySelectorAll('button').forEach(button => button.addEventListener('click', () => selectPart(button.dataset.part)));
  renderTimeline($('mini-timeline'));
  renderTimeline($('full-timeline'), true);
  renderEvidence();
  update();
}

function update() {
  const end = makespan(replay);
  $('time-current').textContent = time.toFixed(1);
  $('scrubber').value = time;
  $('scrubber').style.setProperty('--progress', `${end ? time / end * 100 : 0}%`);
  $('play-icon').textContent = playing ? 'Ⅱ' : '▶';
  $('play-label').textContent = playing ? 'Pause' : time >= end ? 'Replay' : 'Play';
  $('play').setAttribute('aria-label', playing ? 'Pause replay' : time >= end ? 'Replay from start' : 'Play replay');
  $('scene-status').textContent = time >= end ? 'BATCH FINISHED' : playing ? 'FACTORY RUNNING' : time > 0 ? 'REPLAY PAUSED' : 'READY TO REPLAY';
  $('clear-selection').hidden = !selected;
  scene.update(time, selected, playing);
  let completed = 0;
  replay.jobs.forEach(j => {
    const state = jobState(replay, j.id, time);
    if (state.kind === 'complete') completed++;
    const button = [...$('part-list').querySelectorAll('button')].find(b => b.dataset.part === j.id);
    button.classList.toggle('selected', selected === j.id);
    button.setAttribute('aria-pressed', selected === j.id ? 'true' : 'false');
    button.querySelector('.part-state').textContent = state.kind === 'complete' ? 'done' : state.kind === 'processing' ? state.operation.machine : state.kind === 'unscheduled' ? 'missing' : 'waiting';
  });
  $('completed-count').textContent = completed;
  const job = replay.jobs.find(j => j.id === selected);
  if (job) {
    $('part-detail').innerHTML = `<span class="route">${job.operations.map(o => {
      const op = replay.schedule.find(x => x.job === job.id && x.machine === o.machine);
      return `<span><strong>${esc(o.machine)}</strong> ${op ? `${f(op.start)}–${f(op.end)} h` : 'unscheduled'}</span>`;
    }).join('<span aria-hidden="true">→</span>')}</span>`;
  } else if ($('part-detail').dataset.empty !== 'true' || lastAnnouncedTime !== Math.floor(time)) {
    $('part-detail').textContent = 'Select a part to inspect its route and processing times.';
  }
  $('part-detail').dataset.empty = job ? 'false' : 'true';
  lastAnnouncedTime = Math.floor(time);
  document.querySelectorAll('.operation').forEach(b => {
    b.classList.toggle('selected', b.dataset.job === selected);
    b.classList.toggle('dimmed', !!selected && b.dataset.job !== selected);
  });
  document.querySelectorAll('.timeline').forEach(timeline => {
    if (!timeline.clientWidth) return;
    const labelWidth = timeline.querySelector('.timeline-track').getBoundingClientRect().left - timeline.getBoundingClientRect().left;
    timeline.querySelector('.timeline-cursor').style.left = `${labelWidth + (timeline.clientWidth - labelWidth) * (end ? time / end : 0)}px`;
  });
}

function setTab(tab) {
  for (const button of document.querySelectorAll('[data-tab]')) {
    const active = button.dataset.tab === tab;
    button.classList.toggle('active', active);
    button.setAttribute('aria-selected', String(active));
    button.tabIndex = active ? 0 : -1;
    $(`panel-${button.dataset.tab}`).hidden = !active;
  }
  update();
}

for (const button of document.querySelectorAll('[data-tab]')) {
  button.addEventListener('click', () => setTab(button.dataset.tab));
  button.addEventListener('keydown', e => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const tabs = [...document.querySelectorAll('[data-tab]')];
    const i = tabs.indexOf(button);
    const next = e.key === 'Home' ? tabs[0] : e.key === 'End' ? tabs.at(-1) : tabs[(i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
    setTab(next.dataset.tab); next.focus();
  });
}

$('play').addEventListener('click', () => {
  if (time >= makespan(replay)) time = 0;
  playing = !playing; lastFrame = null; update();
});
$('restart').addEventListener('click', () => { playing = false; time = 0; update(); });
$('scrubber').addEventListener('input', e => { playing = false; time = Number(e.target.value); update(); });
$('clear-selection').addEventListener('click', () => { selected = null; update(); });
$('schedule-select').addEventListener('change', e => { $('file-message').textContent = ''; loadReplay(datasets.get(e.target.value)); });
window.addEventListener('resize', update);
document.addEventListener('visibilitychange', () => { if (document.hidden) { playing = false; update(); } });
document.addEventListener('keydown', e => {
  if (e.code === 'Space' && e.target === document.body) { e.preventDefault(); $('play').click(); }
});
$('present').addEventListener('click', async () => {
  if (document.body.classList.contains('presenting')) {
    document.body.classList.remove('presenting');
    if (document.fullscreenElement) await document.exitFullscreen();
  } else {
    document.body.classList.add('presenting');
    try { await document.documentElement.requestFullscreen(); } catch { /* Embedded browsers still get the compact presentation layout. */ }
  }
  $('present').textContent = document.body.classList.contains('presenting') ? 'Exit presentation ↙' : 'Present ↗';
  update();
});
document.addEventListener('fullscreenchange', () => {
  if (!document.fullscreenElement) { document.body.classList.remove('presenting'); $('present').textContent = 'Present ↗'; update(); }
});
$('export-button').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(replay, null, 2) + '\n'], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = `axion-${replay.provenance.kind}-replay.json`; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('file-message').textContent = 'Exported the viewer replay format. Official baseline schedule exports will be produced by the solver pipeline.';
});
$('import-button').addEventListener('click', () => $('import-file').click());
$('import-file').addEventListener('change', async e => {
  const file = e.target.files?.[0];
  if (!file) return;
  try {
    if (file.size > 1_000_000) throw new Error('Replay files must be smaller than 1 MB.');
    const parsed = JSON.parse(await file.text());
    const value = parsed.schema === 'axion-replay.v1' ? parseReplay(parsed) : officialScheduleToReplay(parsed, parsed.instance === 'instance_2x2' ? smallReplay : slideReplay);
    datasets.set('imported', value);
    let option = $('schedule-select').querySelector('[value="imported"]');
    if (!option) { option = document.createElement('option'); option.value = 'imported'; $('schedule-select').append(option); }
    option.textContent = `Imported · ${value.provenance.label}`;
    $('schedule-select').value = 'imported';
    loadReplay(value);
    $('file-message').textContent = validation.feasible ? 'Replay loaded. Schedule feasibility checked; solver provenance is supplied by the file.' : 'Replay loaded with constraint violations. Open Evidence to inspect them.';
    if (!validation.feasible) setTab('evidence');
  } catch (error) { $('file-message').textContent = `Could not load replay: ${error.message}`; }
  e.target.value = '';
});

loadReplay(slideReplay);
function frame(now) {
  if (playing) {
    if (lastFrame !== null) time += Math.min((now - lastFrame) / 1000, .1) * Number($('speed').value) * .65;
    if (time >= makespan(replay)) { time = makespan(replay); playing = false; }
    update();
  }
  lastFrame = now;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
