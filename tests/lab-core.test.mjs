import test from 'node:test';
import assert from 'node:assert/strict';
import {parseCSV,rankScores,labelledMetrics,MAX_ROWS} from '../dist/lab-core.mjs';
import {validateRecords,buildFeatures} from '../dist/inference.mjs';
const header='id,timestamp,sender,receiver,amount,currency';
const row='x,2026-01-01T00:00:00Z,A,B,1.25,CAD';
test('BOM, CRLF, optional label and escaped CSV quoting',()=>{
 const records=parseCSV('\uFEFF'+header+',label\r\n"x,""1",2026-01-01T00:00:00Z,A,B,1.25,CAD,1\r\n');
 assert.equal(records[0].id,'x,"1');assert.equal(records[0].label,1);assert.equal(records[0].amount,1.25);validateRecords(records);
});
test('required headers, duplicate headers and row width are enforced',()=>{
 assert.throws(()=>parseCSV('id,id\na,b'));assert.throws(()=>parseCSV(header+'\nx'));assert.throws(()=>parseCSV(header+',other\n'+row+',x'));assert.throws(()=>parseCSV(header));
});
test('nonfinite, exponent and subcent amounts are rejected',()=>{
 for(const v of ['NaN','Infinity','1e5','1.001','-1'])assert.throws(()=>parseCSV(header+'\n'+row.replace('1.25',v)));
});
test('size, row, cell and broken quote limits are enforced before inference',()=>{
 assert.throws(()=>parseCSV('a'.repeat(5*1024*1024+1)));assert.throws(()=>parseCSV(header+'\n'+Array(MAX_ROWS+1).fill(row).join('\n')));assert.throws(()=>parseCSV(header+'\n'+row.replace('x','x'.repeat(101))));assert.throws(()=>parseCSV(header+'\n"open'));
});
test('unknown and partial labels remain unknown for displayed metrics',()=>{
 const r=parseCSV(header+',label\n'+row+',\n'+row.replace('x,','y,')+',1');validateRecords(r);assert.equal(r[0].label,undefined);assert.deepEqual(labelledMetrics(r,new Set([1])),{precision:null,recall:null});
});
test('label changes cannot affect causal features',()=>{
 const r=parseCSV(header+'\n'+row);assert.deepEqual(buildFeatures(r),buildFeatures(r.map(x=>({...x,label:1}))));
});
test('stable ranking and ceiling review budget have hand-computable answers',()=>{
 const records=Array.from({length:21},(_,i)=>({label:i===0?1:0}));const scores=records.map((_,i)=>i<2?.8:.1);const result=rankScores(records,scores,5);assert.equal(result.k,2);assert.deepEqual(result.ranked.slice(0,2).map(r=>r.index),[0,1]);assert.deepEqual(labelledMetrics(records,result.alerts),{precision:.5,recall:1});
});
test('no-positive recall and edited labels cannot show fabricated metrics',()=>{
 assert.deepEqual(labelledMetrics([{label:0}],new Set([0])),{precision:0,recall:null});assert.deepEqual(labelledMetrics([{label:1}],new Set([0]),false),{precision:null,recall:null});
});
test('ranking rejects undefined scores, wrong sizes and invalid budgets',()=>{
 for(const [scores,budget] of [[[NaN],5],[[1.1],5],[[.2],0],[[.2],11],[[],5]])assert.throws(()=>rankScores([{}],scores,budget));
});
test('duplicate IDs, bad dates, unsupported currency and same-account inputs reject',()=>{
 const r=parseCSV(header+'\n'+row);for(const edit of [{timestamp:'2026-02-30T00:00:00Z'},{currency:'USD'},{receiver:'A'}])assert.throws(()=>validateRecords([{...r[0],...edit}]));assert.throws(()=>validateRecords([r[0],r[0]]));
});
