import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const updateCode=html.split('/* ─── Release updates ─── */')[1].split('/* ─── Markdown / Mermaid ─── */')[0];
const current='a'.repeat(64), next='b'.repeat(64);
function reader(response=next){
  const requests=[],replacements=[],storage=new Map();
  const context=vm.createContext({
    SITE_RELEASE:current, currentChapter:'ch07', URL, Date,
    document:{hidden:false},
    location:{href:'https://example.test/?lang=en#heading-5',replace:url=>replacements.push(url)},
    sessionStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)},
    fetch:async(url,options)=>{requests.push({url,options});if(response instanceof Error)throw response;return {ok:true,json:async()=>({release:response})}},
  });
  vm.runInContext(updateCode,context);
  return {context,requests,replacements,run:()=>vm.runInContext('refreshIfUpdated()',context)};
}
test('a new release bypasses document cache and preserves the current chapter',async()=>{
  const r=reader();assert.equal(await r.run(),true);
  const url=new URL(r.replacements[0]);assert.equal(url.hash,'#ch07');assert.equal(url.searchParams.get('lang'),'en');assert.equal(url.searchParams.get('v'),next);
  assert.equal(r.requests[0].options.cache,'no-store');
  assert.equal(await r.run(),false);assert.equal(r.replacements.length,1);
});
test('unchanged or malformed releases never reload',async()=>{
  for(const value of [current,'invalid',null]){const r=reader(value);assert.equal(await r.run(),false);assert.equal(r.replacements.length,0)}
});
test('offline and hidden readers preserve their current view',async()=>{
  const offline=reader(new Error('offline'));assert.equal(await offline.run(),false);
  const hidden=reader();hidden.context.document.hidden=true;assert.equal(await hidden.run(),false);assert.equal(hidden.requests.length,0);
});
