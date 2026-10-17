// The legacy root viewer keeps root-relative assets when served at /baseline/.
export function baselinePage(html) {
  return html.replace('<head>', '<head>\n  <base href="/" />')
    .replace('href="/stage2/">Full factory ↗', 'href="/catering/">Catering ↗');
}
