// The active shortlist. The first exploration is preserved in docs/design-archive/.
export const variants = [
  {
    id: 'lunar', name: 'Lunar Assembly', genre: 'Orbital workshop',
    note: 'Porcelain consoles, blue steel, and a quiet lunar outpost.', layout: 'orbital',
    ui: ['#243b4e','#536b7b','#8196a3','#bac9d0','#e2eaed','#f1f5f4','#ffffff'],
    land: ['#637284','#586779','#728193'], metal: ['#2c465b','#628198','#a6bdca','#e5eeed'],
    accent: '#355e7c', signal: '#548f9b', floor: '#d5dfe3', grid: '#c4d0d6', floorShine: '#e8edef',
    floorEdge: '#869ba8', road: '#7f8e9b', roadEdge: '#536778', belt: '#42596a', beltEdge: '#2c4253', beltMark: '#8da7b3', badge: '#355e7c', badgeInk: '#f1f5f4',
  },
  {
    id: 'frost', name: 'Frostline Works', genre: 'Alpine workshop',
    note: 'Snow-covered pines, warm work lights, and crisp blue machinery.', layout: 'frostline',
    ui: ['#2c4650','#59737b','#8da5ac','#c2d2d5','#edf2ed','#fbfbf1','#ffffff'],
    land: ['#d7e4e6','#cadadd','#e9f0ee'], metal: ['#304d5c','#638594','#a5bdc4','#e0e9e5'],
    accent: '#3c6b73', signal: '#bd8142', floor: '#e8e9df', grid: '#d6ddd6', floorShine: '#f5f3e8',
    floorEdge: '#a4b8b9', road: '#c1d1d3', roadEdge: '#b1c6cb', belt: '#52717a', beltEdge: '#344f59', beltMark: '#a8c2c5', badge: '#486c76', badgeInk: '#fff8df',
  },
  {
    id: 'blueprint', name: 'Blueprint Bureau', genre: 'Factory drafting room',
    note: 'Solid machines on a deep ink grid, with precise cyan annotations.', layout: 'drafting',
    ui: ['#e0edf1','#abc2ce','#52798f','#244459','#142f43','#1e3e53','#325c73'],
    land: ['#102738','#142e40','#19374b'], metal: ['#2a485e','#537c95','#86afc1','#c4e0e7'],
    accent: '#9bd9e3', signal: '#9bd9e3', floor: '#1b354a', grid: '#254457', floorShine: '#294b60',
    floorEdge: '#41677e', road: '#173246', roadEdge: '#102738', belt: '#25485b', beltEdge: '#102536', beltMark: '#6c9eaf', badge: '#a1d5df', badgeInk: '#19394d',
  },
];
export const findVariant = id => variants.find(v => v.id === id) || variants[0];
const luminance = hex => (.2126 * parseInt(hex.slice(1,3),16) + .7152 * parseInt(hex.slice(3,5),16) + .0722 * parseInt(hex.slice(5,7),16)) / 255;
const band = (value, thresholds) => thresholds.filter(n => value > n).length;
let uiTones;

export function applyVariant(id, root = document.body) {
  const v = findVariant(id);
  root.dataset.variant = v.id;
  root.dataset.layout = v.layout;
  if (!uiTones) {
    uiTones = new Set();
    for (const sheet of document.styleSheets) {
      if (!sheet.href?.endsWith('/style.css')) continue;
      for (const match of [...sheet.cssRules].map(rule => rule.cssText).join('').matchAll(/--ui-([a-f0-9]{6,8})/g)) uiTones.add(match[1]);
    }
  }
  for (const color of uiTones) root.style.setProperty(`--ui-${color}`, v.ui[band(luminance('#' + color), [.29,.43,.57,.68,.78,.88])] + color.slice(6));
  ['ink','muted','edge','shade','surface','light','shine'].forEach((key,i) => root.style.setProperty(`--v-${key}`, v.ui[i]));
  ['ink','muted','wood-dark','wood','wood-light','paper','green'].forEach((key,i) => root.style.setProperty(`--${key}`, [v.ui[0],v.ui[1],v.ui[2],v.ui[3],v.ui[4],v.ui[5],v.accent][i]));
  const colors = {
    ground:v.land[0], grass:v.land[0], 'grass-dark':v.land[1], 'grass-light':v.land[2],
    'world-ink':v.id==='lunar'?'#d0dfe7':v.id==='frost'?'#506e79':'#91b4c6',
    accent:v.accent, signal:v.signal, floor:v.floor, grid:v.grid, 'floor-shine':v.floorShine,
    'floor-edge':v.floorEdge, 'floor-shadow':v.roadEdge, divider:v.floorEdge, road:v.road, 'road-edge':v.roadEdge,
    belt:v.belt, 'belt-edge':v.beltEdge, 'belt-shadow':v.floorEdge, 'belt-mark':v.beltMark,
    badge:v.badge, 'badge-ink':v.badgeInk, highlight:v.floorShine, track:v.grid,
  };
  Object.entries(colors).forEach(([key,value])=>root.style.setProperty(`--v-${key}`,value));
  v.ui.forEach((c,i)=>root.style.setProperty(`--v-tone-${i}`,c));
  v.metal.forEach((c,i)=>root.style.setProperty(`--v-metal-${i}`,c));
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', v.land[0]);
  root.dispatchEvent(new CustomEvent('axion:variant', { bubbles: true }));
  return v;
}

export function styleScene(svg) {
  const semantic = {
    '#b6bf98':'grass', '#a6b388':'grass-dark', '#c5cba7':'grass-light',
    '#d7d5bd':'floor', '#c7c7ae':'grid', '#e2dfc7':'floor-shine', '#ebe7cf':'floor-shine',
    '#c7bb92':'road-edge', '#d2c7a0':'road', '#9aa681':'floor-shadow', '#78816b':'floor-edge', '#a6aa91':'floor-edge', '#a6ac91':'divider',
    '#a5aa8e':'belt-shadow', '#354b40':'belt-edge', '#56675b':'belt', '#82917a':'belt-mark', '#b6bf87':'belt-mark', '#8f9978':'belt-edge', '#c3c99e':'belt-mark',
    '#3c5547':'badge', '#c2cbaa':'highlight', '#b9bda0':'track', '#55765a':'signal',
    '#8d7859':'metal-0', '#ae9469':'metal-1', '#ccb384':'metal-2',
  };
  for (const el of svg.querySelectorAll('[fill], [stroke]')) {
    if (el.closest('.part-token,.original-scenery,.weld-sparks')) continue;
    for (const attr of ['fill','stroke']) {
      const color = el.getAttribute(attr);
      if (!/^#[a-f0-9]{6}$/i.test(color || '')) continue;
      if (el.closest('.machine-art')) {
        const level = Math.max(0, Math.min(2.99, (luminance(color) - .16) * 4));
        const low = Math.floor(level), weight = Math.round((level-low)*100);
        el.setAttribute(attr, `color-mix(in srgb, var(--v-metal-${low}) ${100-weight}%, var(--v-metal-${low+1}))`);
      } else {
        const token = semantic[color] || `tone-${band(luminance(color), [.29,.43,.57,.68,.78,.88])}`;
        el.setAttribute(attr, `var(--v-${token}, ${color})`);
      }
    }
  }
}

const pixelPath = (d,fill,extra='') => `<path d="${d}" fill="${fill}" ${extra}/>`;
const snowPine = (x,y,s=1) => `<g transform="translate(${x} ${y}) scale(${s})">
  ${pixelPath('M-26 15h58v7h-58z','#b1c8cd')}${pixelPath('M-4-6h8v30h-8z','#637e86')}
  ${pixelPath('M-4-61h8v12h9v12h9v12h10v12h8V1h-80v-14h8v-12h10v-12h9v-12h9z','#547581')}
  ${pixelPath('M-4-61h8v12h9v8H-13v-8h9zM-13-37h26v7h9v7h-44v-7h9zM-22-17h44v7h10v7h-64v-7h10z','#eff5f1')}
  ${pixelPath('M-23-2h16v4h-16zM7-24h9v4H7z','#d4e4e4')}</g>`;
const crater = (x,y,s=1) => `<g transform="translate(${x} ${y}) scale(${s})" opacity=".72">
  ${pixelPath('M-24-15h48v6h12v22H24v7h-48v-7h-12V-9h12z','#536274')}
  ${pixelPath('M-24-15h48v5h10v5H18v-5h-36v5h-16v-5h10z','#8491a0')}
  ${pixelPath('M-21-5h42v18h-42z','#5c6b7d')}${pixelPath('M-13 7h26v5h-26z','#6b7a8c')}</g>`;

export function scenery(id, layer='details') {
  const v = findVariant(id);
  if (v.id === 'lunar') {
    if (layer==='terrain') return `<g aria-hidden="true">${crater(95,-47,1.5)}${crater(1006,389,1.5)}${crater(756,-105,.9)}${crater(115,390,.8)}${crater(1030,-40,.75)}
      ${pixelPath('M-200 354h190v6h100v6h65v7H-200zM970 10h300v7h-270v5h-30z','#718092')}
      ${pixelPath('M240-35h12v5h-12zM899 367h14v4h-14zM812-20h7v4h-7zM335 384h6v3h-6z','#8a96a3')}</g>`;
    return `<g class="variant-scenery" aria-hidden="true"><g transform="translate(1043 74)">
      ${pixelPath('M-4-12h8v55h-8zM-20 43h40v6h-40z','#a1b5c1')}${pixelPath('M-35-53h70v8H25v12H12v9h-24v-9h-13v-12h-10z','#d2dfe4')}
      ${pixelPath('M-26-49h52v6H14v10h-28v-10h-12z','#728fa4')}<path stroke="#d2dfe4" stroke-width="3" d="M0-38l20-26"/>
      ${pixelPath('M18-68h6v6h-6z','#e9c17d')}</g>
      <g transform="translate(71 328)">${pixelPath('M-39-19h78v39h-78z','#3d5368')}${pixelPath('M-35-24h70v5h-70z','#9bafbd')}
      ${[-27,-6,15].map(x=>pixelPath(`M${x}-13h15v25h-15z`,'#527891')+pixelPath(`M${x+2}-10h11v2h-11z`,'#88b0c4')).join('')}
      ${pixelPath('M-25 20h5v13h-5zM20 20h5v13h-5z','#40576b')}</g>
      <g fill="#536d80"><path d="M184 332h12v4h-12zM904 24h14v4h-14z"/></g></g>`;
  }
  if (v.id === 'frost') {
    if (layer==='terrain') return `<g aria-hidden="true">
      ${pixelPath('M-200 0H95v9h44v9H-200zM935-2h400v13H976v9h-41zM-200 349H95v9h41v10h-336zM947 345h400v24H922v-10h25z','#eaf1ef')}
      ${pixelPath('M-100 28H80v4h-180zM992 37h190v4H992zM20 385h145v4H20zM930 393h180v4H930z','#c4d8dc')}
      ${snowPine(51,80,.95)}${snowPine(1110,94,1.15)}${snowPine(1082,366,.95)}${snowPine(54,363,1.1)}${snowPine(270,-48,.7)}${snowPine(864,-55,.8)}
      ${pixelPath('M26 326h35v5H26zM1045 57h34v5h-34z','#f7f8ed')}</g>`;
    return `<g class="variant-scenery" aria-hidden="true">
      <g transform="translate(1037 105)">${pixelPath('M-3-40h6v66h-6zM-10 26h20v5h-20z','#6e8992')}${pixelPath('M-14-47h28v15h-28z','#536d79')}${pixelPath('M-10-44h20v9h-20z','#efcc89')}${pixelPath('M-19-51h38v5h-38z','#f6f6eb')}</g>
      <g transform="translate(92 342)">${pixelPath('M-3-37h6v46h-6zM-11 9h22v5h-22z','#6e8992')}${pixelPath('M-13-44h26v13h-26z','#536d79')}${pixelPath('M-9-41h18v7h-18z','#efcc89')}${pixelPath('M-18-48h36v5h-36z','#f6f6eb')}</g>
      ${pixelPath('M149 58h815v4H149zM145 63h7v42h-7zM967 280h6v35h-6zM153 314h180v5H153z','#f7f6ed')}
      ${pixelPath('M164 322h115v3H164zM840 48h117v3H840z','#b9cdd1')}</g>`;
  }
  if (layer==='terrain') return `<g aria-hidden="true" stroke="#2d4e64" stroke-width="1" opacity=".45"><path d="M40-200v900M1080-200v900M-500 0h2200M-500 380h2200"/></g>`;
  return `<g class="variant-scenery drafting-guides" aria-hidden="true" fill="none" stroke="#759eaf" stroke-width="1" opacity=".65">
    <path d="M156 39h808M156 33v12M964 33v12M137 61v251M131 61h12M131 312h12"/>
    <path d="M166 40l-7-3m7 3-7 3M954 40l7-3m-7 3 7 3"/>
    <path d="M143 53h16M151 45v16M959 53h16M967 45v16M143 320h16M151 312v16M959 320h16M967 312v16"/>
    <path d="M1008 281h63M1008 286v-10M1071 286v-10"/>
    <g stroke="#466d84" opacity=".7"><path d="M174 331h18m6 0h6m6 0h6M903 46h15m6 0h6"/></g>
  </g>`;
}
