// Ten art directions share one live replay; the original remains available as a reference.
export const variants = [
  { id: 'copper', name: 'Copper Canyon', genre: 'Frontier crafting', note: 'Sun-baked sand, copper machinery, trading-post timber.', layout: 'frontier', motif: 'cactus', ui: ['#372a27','#775443','#99664a','#ba8259','#d7ab7a','#f0d3a0','#fff0c8'], land: ['#d6ad77','#c49764','#efd09a'], foliage: ['#52674b','#71834e','#9aa362'], metal: ['#634336','#966644','#cc9665','#f1c58b'], accent: '#7b4533' },
  { id: 'lunar', name: 'Lunar Assembly', genre: 'Space colony sim', note: 'Moon dust, porcelain consoles, a quiet orbital workshop.', layout: 'orbital', motif: 'satellite', ui: ['#23364c','#526779','#8294a4','#b4c3cd','#dce6e9','#edf5f4','#ffffff'], land: ['#69788e','#5d6b81','#7f8da0'], foliage: ['#3d4f6e','#59718d','#92adc2'], metal: ['#3b506c','#718ba2','#b5cbd5','#e7f0ec'], accent: '#315e8a' },
  { id: 'arcade', name: 'Midnight Arcade', genre: '16-bit cyber factory', note: 'Electric cyan, hot-pink circuits, midnight CRT glass.', layout: 'arcade', motif: 'city', ui: ['#f7e6ff','#b8a9d1','#775b9d','#2e244f','#201a39','#493567','#75518d'], land: ['#17182f','#22203c','#2d254b'], foliage: ['#402c64','#754080','#b85a97'], metal: ['#35345f','#525482','#8493b3','#c5e4eb'], accent: '#ff73bf' },
  { id: 'frost', name: 'Frostline Works', genre: 'Arctic survival', note: 'Snowdrifts, blue steel, warm lights in the polar night.', layout: 'minimal', motif: 'crystal', ui: ['#263e50','#547484','#83a7b4','#b2d0d7','#dcecf0','#f5faf7','#ffffff'], land: ['#dce9e7','#c9dcdc','#f2f6ed'], foliage: ['#456f76','#73999a','#a6c5bd'], metal: ['#355667','#65899b','#a5bfc7','#e1eff0'], accent: '#397084' },
  { id: 'moss', name: 'Moss & Mechanism', genre: 'Ancient forest RPG', note: 'An old stone workshop reclaimed by the forest.', layout: 'ruins', motif: 'ruins', ui: ['#263d2d','#5c7051','#7d8557','#a5a77b','#c7cf9f','#e4e7bb','#f4f3d3'], land: ['#7d9968','#6d8959','#98ad78'], foliage: ['#304f3d','#4e7350','#82a368'], metal: ['#40554b','#6c7c64','#a0ac86','#d2d7ae'], accent: '#3e6145' },
  { id: 'sakura', name: 'Sakura Atelier', genre: 'Cozy crafting RPG', note: 'Rose-paper menus, blossom trees, a soft spring afternoon.', layout: 'atelier', motif: 'gate', ui: ['#573e4e','#8b6673','#b28a91','#d5aeb1','#efd4cc','#fff0df','#fff9ed'], land: ['#d4c8b4','#bfc1a0','#e4d9c6'], foliage: ['#9c6d82','#cf92a4','#f2c4cc'], metal: ['#77616a','#a18a8c','#c4b5aa','#e9ddd0'], accent: '#966079' },
  { id: 'abyss', name: 'Abyssal Station', genre: 'Deep-sea exploration', note: 'Submarine instrument panels and bioluminescent coral.', layout: 'submarine', motif: 'coral', ui: ['#e3f4df','#a0c8bc','#548e91','#24575e','#163c48','#326b70','#579a95'], land: ['#143642','#194650','#25555b'], foliage: ['#33586b','#497c85','#7db9ae'], metal: ['#244e59','#467e84','#81b1ac','#bbd9c5'], accent: '#b6e8ab' },
  { id: 'forge', name: 'Ember Forge', genre: 'Industrial dungeon', note: 'Coal-black iron, hazard stripes, rivers of molten ore.', layout: 'foundry', motif: 'pipes', ui: ['#f5e6c9','#c1a48c','#7c5c50','#403335','#2c272b','#60443a','#956244'], land: ['#3b3439','#302c33','#514049'], foliage: ['#503a3b','#775044','#ad6b47'], metal: ['#3a3942','#64606b','#a39894','#d7c2a3'], accent: '#ffb052' },
  { id: 'pocket', name: 'Pocket Factory', genre: 'Handheld classic', note: 'Four-color LCD sprites and the heft of a pocket console.', layout: 'pocket', motif: 'pixels', ui: ['#243d27','#405b35','#6b8346','#8c9d58','#acb971','#c9d58b','#e0e5a7'], land: ['#acb971','#8c9d58','#c9d58b'], foliage: ['#243d27','#405b35','#6b8346'], metal: ['#243d27','#405b35','#8c9d58','#c9d58b'], accent: '#314d2e' },
  { id: 'blueprint', name: 'Blueprint Bureau', genre: 'Technical strategy', note: 'Cobalt drafting paper, precise linework, engineer’s notes.', layout: 'drafting', motif: 'draft', ui: ['#edf7f1','#b7d7df','#6b9bb7','#2c597b','#183e63','#366c8e','#6293ab'], land: ['#214d76','#285980','#32668b'], foliage: ['#2a5a7d','#4e86a2','#8dbac9'], metal: ['#326386','#598fa8','#9fcbd3','#e0f1e9'], accent: '#e6d79c' },
];

export const original = { id: 'original', name: 'Original Workshop', genre: 'Current design', note: 'The original timber workshop, for reference.' };
export const findVariant = id => variants.find(v => v.id === id) || original;
const luminance = hex => { const n = hex.slice(1,7); return (.2126 * parseInt(n.slice(0,2),16) + .7152 * parseInt(n.slice(2,4),16) + .0722 * parseInt(n.slice(4,6),16)) / 255; };
const band = (value, thresholds) => thresholds.filter(n => value > n).length;

export function applyVariant(id, root = document.body) {
  const v = findVariant(id);
  root.dataset.variant = v.id;
  root.dataset.layout = v.layout || 'original';
  if (v.id === 'original') { root.removeAttribute('style'); root.dispatchEvent(new CustomEvent('axion:variant', { bubbles: true })); return v; }
  // Each original UI tone has a named fallback in style.css. Keep alpha channels intact.
  for (const sheet of document.styleSheets) {
    if (!sheet.href?.endsWith('/style.css')) continue;
    const css = [...sheet.cssRules].map(rule => rule.cssText).join('');
    const colors = new Set([...css.matchAll(/--ui-([a-f0-9]{6,8})/g)].map(m => m[1]));
    for (const color of colors) root.style.setProperty(`--ui-${color}`, v.ui[band(luminance('#' + color), [.29,.43,.57,.68,.78,.88])] + color.slice(6));
  }
  ['ink','muted','edge','shade','surface','light','shine'].forEach((key,i) => root.style.setProperty(`--v-${key}`, v.ui[i]));
  ['ink','muted','wood-dark','wood','wood-light','paper','green'].forEach((key,i) => root.style.setProperty(`--${key}`, [v.ui[0],v.ui[1],v.ui[2],v.ui[3],v.ui[4],v.ui[5],v.accent][i]));
  v.ui.forEach((c,i) => root.style.setProperty(`--v-tone-${i}`, c));
  root.style.setProperty('--v-accent', v.accent);
  root.style.setProperty('--v-ground', v.land[0]);
  // Scene colors are semantic, so jobs retain their identifying colors.
  root.style.setProperty('--v-grass', v.land[0]);
  root.style.setProperty('--v-grass-dark', v.land[1]);
  root.style.setProperty('--v-grass-light', v.land[2]);
  v.foliage.forEach((c,i) => root.style.setProperty(`--v-leaf-${i}`, c));
  v.metal.forEach((c,i) => root.style.setProperty(`--v-metal-${i}`, c));
  root.dispatchEvent(new CustomEvent('axion:variant', { bubbles: true }));
  return v;
}

export function styleScene(svg) {
  const grass = { '#b6bf98':'grass', '#a6b388':'grass-dark', '#c5cba7':'grass-light' };
  const leaves = ['#4f6d47','#4a6650','#6b8755','#608063','#8b9e68','#759570'];
  for (const el of svg.querySelectorAll('[fill], [stroke]')) {
    if (el.closest('.part-token')) continue;
    for (const attr of ['fill','stroke']) {
      const color = el.getAttribute(attr);
      if (!/^#[a-f0-9]{6}$/i.test(color || '')) continue;
      let token;
      if (grass[color]) token = grass[color];
      else if (leaves.includes(color)) token = `leaf-${Math.floor(leaves.indexOf(color) / 2)}`;
      else if (el.closest('.machine-art')) {
        const level = Math.max(0, Math.min(2.99, (luminance(color) - .16) * 4));
        const low = Math.floor(level), weight = Math.round((level-low)*100);
        el.setAttribute(attr, `color-mix(in srgb, var(--v-metal-${low}, ${color}) ${100-weight}%, var(--v-metal-${low+1}, ${color}))`);
        continue;
      } else token = `tone-${band(luminance(color), [.29,.43,.57,.68,.78,.88])}`;
      el.setAttribute(attr, `var(--v-${token}, ${color})`);
    }
  }
}

export function scenery(id) {
  const v = findVariant(id);
  if (v.id === 'original') return '';
  const colors = v.metal;
  const block = (x,y,w,h,c) => `<path fill="${c}" d="M${x} ${y}h${w}v${h}h-${w}z"/>`;
  const prop = (x,y,flip=1) => {
    let art = '';
    switch (v.motif) {
      case 'cactus': art = `<path fill="${v.foliage[0]}" d="M-8-61h16v70H-8zM-30-40h12v28h17V0h-29zM18-53h12v32H4v-12h14z"/>${block(-3,-57,4,61,v.foliage[2])}${block(-30,9,65,7,v.land[1])}`; break;
      case 'satellite': art = `<path fill="${colors[2]}" d="M-3-20h6v48H-3zM-35-60h70v10H25v12H10v10H-5v-10h-15v-12h-15z"/><path fill="${colors[0]}" d="M-24-56h48v6H15v10H0v-10h-24z"/><path stroke="${colors[3]}" stroke-width="3" d="M0-48l22-25"/>${block(-18,28,36,7,colors[1])}`; break;
      case 'city': art = [-35,-10,22].map((a,i)=>block(a,-45-i*16,24,80+i*16,colors[0])+Array.from({length:4},(_,j)=>block(a+5,-36-i*16+j*15,5,5,j%2?v.accent:'#6ae5e5')).join('')).join(''); break;
      case 'crystal': art = `<path fill="${colors[1]}" d="M-32 15v-33l12-16 12 16V15zM-7 15v-62L9-71l15 24v62zM25 15v-27l10-15 11 15v27z"/><path fill="${colors[3]}" d="M-7-47 9-71v86H-7zM-32-18l12-16v49h-12z"/>`; break;
      case 'ruins': art = `<path fill="${colors[1]}" d="M-45 21v-73h17v-12h56v12h17v73H24v-62h-48v62z"/><path fill="${colors[2]}" d="M-45-52h17v-12h56v12h17v7H-45z"/><path fill="${v.foliage[0]}" d="M-43-48h10v28h12v9h-17v30h-8zM12-61h11v28H12z"/>`; break;
      case 'gate': art = `<path fill="${v.accent}" d="M-40-50h80v8H-40zM-31-42h8v62h-8zM23-42h8v62h-8zM-47-63h94v10H-47zM-36-24h72v6H-36z"/>${block(-52,-68,104,5,colors[0])}`; break;
      case 'coral': art = `<path fill="${v.foliage[2]}" d="M-4 21v-64H5v25h15v-27h8v36H5v30zM-4-6h-25v-30h8v21h17z"/><path fill="${v.accent}" d="M-38 22V-4h9v-16h8v16h-7v26zM27 22V3h10v-18h8V9H35v13z"/>${[-60,-85,-110].map((y,i)=>`<rect x="${i*15}" y="${y}" width="7" height="7" fill="none" stroke="${colors[2]}" stroke-width="2"/>`).join('')}`; break;
      case 'pipes': art = `<path fill="${colors[0]}" d="M-33 22v-72h17v-12h43v84H10v-67H-16v67z"/><path fill="${colors[2]}" d="M-33-50h7v72h-7zM10-62h17v7H10z"/>${block(-39,-28,28,8,colors[1])}${block(4,-10,29,8,colors[1])}<path fill="${v.accent}" d="M-47 25h102v6H-47zM-37 36h12v6h-12zM0 36h34v6H0z"/>`; break;
      case 'pixels': art = `<path fill="${colors[0]}" d="M-24-36h48v12h12v36H24v12h-48V12h-12v-36h12z"/><path fill="${colors[2]}" d="M-12-24h24v12h-24zM-24 0h12v12h-12zM12 0h12v12H12z"/>`; break;
      case 'draft': art = `<g fill="none" stroke="${colors[3]}" stroke-width="2"><path d="M-38 22v-65h76v65zM-48 32h96M-48-53h96M-48-58v10M48-58v10M-38-43l76 65M38-43l-76 65"/><circle cy="-10" r="20"/></g>`; break;
    }
    return `<g transform="translate(${x} ${y}) scale(${flip} 1)">${art}</g>`;
  };
  return `<g class="variant-scenery" aria-hidden="true">${prop(99,88)}${prop(1019,361,-1)}${prop(285,-65)}${prop(822,450,-1)}${v.motif==='city'||v.motif==='satellite'?Array.from({length:28},(_,i)=>block((i*137)%1120,-120+(i*47)%580,3,3,colors[2])).join(''):''}</g>`;
}
