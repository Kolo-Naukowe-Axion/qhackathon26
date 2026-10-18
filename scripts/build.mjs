import { baselinePage } from './baseline-page.mjs';
import { cp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';

const output = new URL('../dist/', import.meta.url);
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(new URL('../presentation/', import.meta.url), output, { recursive: true });
await mkdir(new URL('baseline/',output),{recursive:true});
await writeFile(new URL('baseline/index.html',output),baselinePage(await readFile(new URL('../presentation/index.html',import.meta.url),'utf8')));
await writeFile(new URL('index.html',output),'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Axion Kitchen · QPoland 2026 winner</title><meta property="og:title" content="Axion Kitchen · QPoland 2026 winner"><meta property="og:description" content="Main prize winner and joint first in the VeloxQ award. Catering production scheduling with QAOA, VQE and VeloxQ."><meta property="og:image" content="https://qfactoria.com/assets/branding/axion-kitchen-winner.jpg"><meta property="og:type" content="website"><meta name="twitter:card" content="summary_large_image"><meta http-equiv="refresh" content="0;url=/catering/"><link rel="canonical" href="/catering/"></head><body><a href="/catering/">Open Axion Kitchen</a></body></html>\n');
console.log('Static site built in dist/');
