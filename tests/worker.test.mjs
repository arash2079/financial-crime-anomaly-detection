import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Worker} from 'node:worker_threads';
import {once} from 'node:events';
const load=f=>JSON.parse(fs.readFileSync(new URL('../dist/artifacts/'+f,import.meta.url),'utf8'));
const demo=load('demo.json'),models=load('models.json'),fixture=load('parity-fixture.json');
async function create(t){const w=new Worker(new URL('./worker-harness.mjs',import.meta.url),{workerData:{module:new URL('../dist/inference-worker.mjs',import.meta.url).href}});t.after(()=>w.terminate());const [ready]=await once(w,'message');assert.equal(ready.ready,true);return w;}
async function message(w,data){const pending=once(w,'message');w.postMessage(data);return (await pending)[0];}
test('actual inference worker returns full Python-reference LR and RF scores',async t=>{
 const w=await create(t);for(const model of ['forest','logistic']){const output=await message(w,{records:demo.records,models,model});assert.equal(output.scores.length,1044);assert.equal(output.features.length,1044);const expected=model==='forest'?fixture.forestScores:fixture.logisticScores;for(let j=0;j<fixture.recordIndices.length;j++)assert.ok(Math.abs(output.scores[fixture.recordIndices[j]]-expected[j])<1e-10);}
});
test('worker reports invalid input, unknown models and resource limits without fake success',async t=>{
 const w=await create(t);for(const data of [{records:[{...demo.records[0],amount:NaN}],models,model:'forest'},{records:demo.records,models,model:'unknown'},{records:Array(5001).fill(demo.records[0]),models,model:'forest'}]){const result=await message(w,data);assert.equal(typeof result.error,'string');assert.equal(result.scores,undefined);}
 const valid=await message(w,{records:demo.records,models,model:'forest'});assert.equal(valid.scores.length,1044);
});
