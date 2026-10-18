import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {baselinePage} from '../scripts/baseline-page.mjs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('production starts with catering while preserving the original viewer',()=>{
 const config=JSON.parse(read('vercel.json'));
 assert.deepEqual(config.redirects.find(r=>r.source==='/'),{source:'/',destination:'/catering/',permanent:false});
 const legacy=baselinePage(read('presentation/index.html'));
 assert.match(legacy,/<base href="\/"\s*\/>/);
 assert.match(legacy,/id="factory-scene"/);
 assert.match(legacy,/src="\.\/app.js"/);
 assert.doesNotMatch(legacy,/href="\/stage2\/"/);
});
test('kitchen links back to Stage 1 without publishing private speaker materials',()=>{
 const html=read('presentation/catering/index.html');
 assert.match(html,/href="\/baseline\/"/);
 assert.match(html,/href="\/problem-explanation\/"/);
 assert.doesNotMatch(html,/catering-showcase|CATERING_QA|CATERING_VOICEOVER/);
});
