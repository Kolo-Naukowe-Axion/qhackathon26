import { jobState } from './model.js';

export const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const tree = (x, y, scale = 1) => `<g transform="translate(${x} ${y}) scale(${scale})"><path fill="#6c7452" opacity=".19" d="M-23 19h47v12h-47z"/><path fill="#7f6247" d="M-5 0h10v27H-5z"/><path fill="#4f6d47" d="M-10-44h20v10h12v12h10v24h-10v10h-44v-10h-10v-24h10v-12h12z"/><path fill="#6b8755" d="M-10-44h20v10h12v12h-20v12h-24v-12h12z"/><path fill="#8b9e68" d="M-10-35h12v10h-12z"/></g>`;
const pine = (x, y) => `<g transform="translate(${x} ${y})"><path fill="#7f6247" d="M-4 0h8v24h-8z"/><path fill="#4a6650" d="M-5-55h10v12h10v12h10v12h10v17h-70v-17h10v-12h10v-12h10z"/><path fill="#608063" d="M-5-55h10v12h10v12h-13v12h-18v-12h11z"/><path fill="#759570" d="M-5-41h8v12h-8z"/></g>`;

function machineArt(index) {
  const base = `<path fill="#535f5c" d="M-70 48h140v16H-70z"/><path fill="#8c9990" d="M-70 39h140v14H-70z"/><path fill="#c3c9b9" d="M-67 39h134v5H-67z"/><path fill="#434f4c" d="M-58 64h14v8h-14zm103 0h14v8H45z"/>`;
  if (index === 0) return `${base}<path fill="#687f7a" d="M-60-10h33v49h-33zM25-5h35v44H25z"/><path fill="#91a39a" d="M-60-16h33v9h-33zM25-11h35v9H25z"/><path fill="#bdc4b5" d="M-27 3h51v20h-51z"/><path fill="#dce0ce" d="M-27 3h51v5h-51z"/><path class="lathe-shaft" fill="#4b625c" d="M-12-1h10v28h-10zM7-1h6v28H7z"/><path fill="#465b55" d="M-58-8h20v17h-20z"/><path fill="#a8bf91" d="M-54-4h12v8h-12z"/><path fill="#303f3c" d="M38 7h13v13H38z"/><path fill="#b8c1ac" d="M42 3h5v21h-5zM35 10h19v5H35z"/><path fill="#d2b777" d="M-21 32h40v6h-40z"/>`;
  if (index === 1) return `${base}<path fill="#5c7773" d="M-48-44h35v83h-35z"/><path fill="#7c9890" d="M-48-44h80v17h-80z"/><path fill="#a4b4a7" d="M-48-50h80v7h-80z"/><path fill="#3c5350" d="M-39-30h15v51h-15z"/><g class="mill-head"><path fill="#91a79e" d="M3-28h23v27H3z"/><path fill="#455c56" d="M9-1h11v18H9z"/><path fill="#c5cfbb" d="M12 9h5v15h-5z"/></g><path fill="#c9cdbb" d="M-19 25h65v9h-65z"/><path fill="#7d938b" d="M-10 19h44v6h-44z"/><path fill="#d0b378" d="M-7 17h27v5H-7z"/><path fill="#3d5550" d="M-57-20h16v23h-16z"/><path fill="#a7bf91" d="M-54-17h10v9h-10z"/>`;
  return `${base}<path fill="#6d7d77" d="M-63-17h30v56h-30z"/><path fill="#98a299" d="M-63-23h30v8h-30z"/><path fill="#374b47" d="M-56-12h16v11h-16z"/><path fill="#a4bc86" d="M-53-9h10v5h-10z"/><path fill="#484f49" d="M-30 12h16v7h-16zM-17 12h7v15h-7zM-10 22h23v7h-23z"/><path fill="#9c8c68" d="M5-5h43v12H5z"/><path fill="#b7a37a" d="M5-11h43v6H5z"/><path fill="#a4b2a4" d="M14-48h13v23H14zM20-30h28v11H20zM38-25h12v18H38z"/><path fill="#435e55" d="M10 7h6v32h-6zM38 7h6v32h-6z"/><g class="weld-sparks"><path fill="#f8edb2" d="M22-6h12v9H22zM14-18h5v8h-5zM38-15h5v6h-5zM29-25h4v8h-4z"/><path fill="#fffce7" d="M25-9h6v10h-6z"/></g>`;
}

export function createScene(container, replay, onSelect) {
  const stations = replay.machines.length === 2 ? [355, 755] : [280, 560, 840];
  container.innerHTML = `<svg viewBox="0 0 1120 388" class="shop-svg" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="shop-title shop-desc">
    <title id="shop-title">An illustrated ${replay.machines.length}-machine factory</title><desc id="shop-desc">Parts move through the displayed stations. Use the replay time slider or the part buttons below to inspect their state.</desc>
    <defs>
      <pattern id="grass" width="64" height="64" patternUnits="userSpaceOnUse"><rect width="64" height="64" fill="#b6bf98"/><path fill="#a6b388" d="M7 13h3v4H7zm34 28h3v4h-3zM20 52h5v2h-5zM56 9h4v2h-4z"/><path fill="#c5cba7" d="M12 36h6v3h-6zm34-11h5v3h-5z"/></pattern>
      <pattern id="floor" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="#d7d5bd"/><path fill="none" stroke="#c7c7ae" stroke-width="1" d="M0 0h40v40H0z"/><path fill="#e2dfc7" d="M2 2h35v2H2z"/></pattern>
      <pattern id="belt" width="18" height="18" patternUnits="userSpaceOnUse"><rect width="18" height="18" fill="#56675b"/><path fill="#82917a" d="m2 3 7 5-7 5v-4l3-1-3-1z"/></pattern>
    </defs>
    <rect width="1120" height="388" fill="url(#grass)"/>
    <path fill="#c7bb92" d="M0 185h1120v94H0zM1010 185h75v203h-75z"/>
    <path fill="#d2c7a0" d="M0 193h1120v77H0zM1020 193h56v195h-56z"/>
    <path fill="#9aa681" d="M142 65h836v258H142z"/><path fill="#78816b" d="M150 65h820v255H150z"/>
    <rect x="156" y="61" width="808" height="251" fill="url(#floor)"/>
    <path stroke="#ebe7cf" stroke-width="4" d="M158 65h804M158 65v242"/><path stroke="#a6aa91" stroke-width="5" d="M158 310h806M963 65v246"/>
    <path stroke="#a6ac91" stroke-width="2" stroke-dasharray="5 6" d="M410 80v211M700 80v211"/>
    <path fill="#a5aa8e" d="M165 229h790v34H165z"/><path fill="#354b40" d="M132 236h856v26H132z"/>
    <path fill="url(#belt)" d="M135 240h850v17H135z"/><path class="belt-motion" fill="none" stroke="#b6bf87" stroke-width="2" stroke-dasharray="2 18" d="M135 243h850"/>
    <path fill="#8f9978" d="M135 234h850v3H135zm0 26h850v3H135z"/>
    <g fill="#c3c99e"><path d="m177 247 6 3-6 3zm269 0 6 3-6 3zm283 0 6 3-6 3zm225 0 6 3-6 3z"/></g>
    <g fill="#8d7859"><path d="M51 217h64v66H51zM1002 217h65v66h-65z"/></g><g fill="#ae9469"><path d="M47 212h72v57H47zM998 212h73v57h-73z"/></g>
    <g fill="#ccb384"><path d="M50 215h66v6H50zm0 24h66v4H50zm0 23h66v4H50zM1001 215h67v6h-67zm0 24h67v4h-67zm0 23h67v4h-67z"/></g>
    <text x="83" y="201" class="scene-label" text-anchor="middle">IN</text><text x="1035" y="201" class="scene-label" text-anchor="middle">OUT</text>
    ${replay.machines.map((m, i) => `<g class="machine" data-station="${i}" transform="translate(${stations[i]} 161)">
      <rect class="station-highlight" x="-93" y="-48" width="186" height="120" fill="#c2cbaa" opacity="0"/>
      <g class="machine-art">${machineArt(i)}</g>
      <rect x="-12" y="-82" width="24" height="22" fill="#3c5547"/><text x="0" y="-66" class="machine-code" text-anchor="middle">${escapeHtml(m.id)}</text>
      <text x="0" y="-91" class="machine-name" text-anchor="middle">${escapeHtml(m.name.toUpperCase())}</text>
      <rect x="-55" y="122" width="110" height="4" fill="#b9bda0"/><rect class="machine-progress" x="-55" y="122" width="0" height="4" fill="#55765a"/>
      <text class="machine-status" x="0" y="112" text-anchor="middle">Idle</text>
    </g>`).join('')}
    <g class="landscape" aria-hidden="true">${tree(58, 104, 1.05)}${pine(112, 83)}${tree(1036, 96, .95)}${pine(1090, 134)}${tree(49, 347, 1.2)}${tree(112, 340, .8)}${pine(968, 365)}${tree(1091, 350, .8)}
    <g fill="#89996c"><path d="M170 341h25v10h-25zm8-6h10v6h-10zM742 343h28v10h-28zm10-7h12v8h-12zM407 25h24v9h-24z"/></g>
    <g fill="#e9db9e"><path d="M141 29h4v4h-4zM148 36h4v4h-4zM998 340h4v4h-4zM1005 347h4v4h-4zM788 24h4v4h-4z"/></g>
    <g fill="#95a682"><path d="M198 34h7v6h-7zm-4 6h16v4h-16zM623 348h9v6h-9zm-5 6h20v4h-20z"/></g>
    <g transform="translate(502 332)"><path fill="#7c6a4d" d="M0 0h81v8H0zm7 8h6v10H7zm59 0h6v10h-6z"/><path fill="#b4a078" d="M0-5h81v5H0z"/><path fill="#7c6a4d" d="M7-18h6v16H7zm59 0h6v16h-6z"/><path fill="#b4a078" d="M0-23h81v7H0z"/></g>
    </g>
    ${replay.jobs.map((j, i) => `<g class="part-token" data-token="${i}" role="button" tabindex="0" aria-label="Follow part ${escapeHtml(j.id)}" transform="translate(80 235)">
      <rect class="part-halo" x="-18" y="-18" width="36" height="36" fill="none" stroke="#fdfbe8" stroke-width="3" opacity="0"/>
      <path fill="#394e3e" opacity=".28" d="M-11 8h25v7h-25z"/><rect x="-12" y="-12" width="24" height="24" fill="${j.color}"/><path fill="#ffffff" opacity=".3" d="M-12-12h24v4h-24z"/><path fill="#17261d" opacity=".22" d="M8-8h4v20H8zM-12 8h20v4h-20z"/>
      <text y="4" text-anchor="middle" class="token-text">${escapeHtml(j.id)}</text>
    </g>`).join('')}
  </svg>`;
  const svg = container.querySelector('svg');
  const tokens = [...container.querySelectorAll('.part-token')];
  tokens.forEach((token, index) => {
    token.addEventListener('click', () => onSelect(replay.jobs[index].id));
    token.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(replay.jobs[index].id); } });
  });
  return {
    update(time, selected, playing) {
      svg.classList.toggle('playing', playing);
      replay.machines.forEach((machine, index) => {
        const active = replay.schedule.find(o => o.machine === machine.id && o.start <= time && time < o.end);
        const group = container.querySelector(`[data-station="${index}"]`);
        group.classList.toggle('active', !!active);
        group.querySelector('.machine-status').textContent = active ? `${active.job} · processing` : 'Idle';
        group.querySelector('.machine-progress').setAttribute('width', active ? 110 * (time - active.start) / (active.end - active.start) : 0);
      });
      replay.jobs.forEach((job, i) => {
        const state = jobState(replay, job.id, time);
        let x = 80, y = 230 + i * 17;
        if (state.kind === 'processing') { x = stations[replay.machines.findIndex(m => m.id === state.operation.machine)]; y = 247; }
        if (state.kind === 'waiting' && state.after) {
          const nextIndex = replay.machines.findIndex(m => m.id === state.next.machine);
          const fraction = Math.min(1, (time - state.after.end) / Math.min(.4, state.next.start - state.after.end));
          const previousX = stations[replay.machines.findIndex(m => m.id === state.after.machine)];
          x = previousX + (stations[nextIndex] - 82 - previousX) * fraction;
          y = 230 + i * 11;
        }
        if (state.kind === 'complete') { x = 1035; y = 228 + i * 17; }
        tokens[i].setAttribute('transform', `translate(${x} ${y})`);
        tokens[i].classList.toggle('selected', selected === job.id);
        tokens[i].classList.toggle('dimmed', !!selected && selected !== job.id);
      });
    }
  };
}
