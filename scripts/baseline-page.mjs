// The legacy root viewer keeps root-relative assets when served at /baseline/.
export function baselinePage(html) {
  return html.replace('<head>', '<head>\n  <base href="/" />')
    .replaceAll(/href="\/stage2\/"([^>]*)>Full factory ↗/g, 'href="/catering/"$1>Catering ↗');
}
