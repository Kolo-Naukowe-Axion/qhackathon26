// Lunar Assembly is the fixed appearance. Alternative directions live in docs/design-archive/.
export function initializeLunar() {
  document.body.dataset.theme = 'lunar';
  const url = new URL(location.href);
  const legacy = ['variant', 'gallery', 'preview'];
  if (legacy.some(key => url.searchParams.has(key))) {
    legacy.forEach(key => url.searchParams.delete(key));
    history.replaceState(null, '', url);
  }
}
const luminance = hex => (.2126 * parseInt(hex.slice(1,3),16) + .7152 * parseInt(hex.slice(3,5),16) + .0722 * parseInt(hex.slice(5,7),16)) / 255;
const band = (value, thresholds) => thresholds.filter(n => value > n).length;

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
    if (el.closest('.part-token,.weld-sparks')) continue;
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
const crater = (x,y,s=1) => `<g transform="translate(${x} ${y}) scale(${s})" opacity=".72">
  ${pixelPath('M-24-15h48v6h12v22H24v7h-48v-7h-12V-9h12z','#536274')}
  ${pixelPath('M-24-15h48v5h10v5H18v-5h-36v5h-16v-5h10z','#8491a0')}
  ${pixelPath('M-21-5h42v18h-42z','#5c6b7d')}${pixelPath('M-13 7h26v5h-26z','#6b7a8c')}</g>`;

export function scenery(layer='details') {
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
