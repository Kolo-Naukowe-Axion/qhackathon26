import { baselinePage } from './baseline-page.mjs';
import { cp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';

const output = new URL('../dist/', import.meta.url);
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(new URL('../presentation/', import.meta.url), output, { recursive: true });
await mkdir(new URL('baseline/',output),{recursive:true});
await writeFile(new URL('baseline/index.html',output),baselinePage(await readFile(new URL('../presentation/index.html',import.meta.url),'utf8')));
console.log('Static site built in dist/');
