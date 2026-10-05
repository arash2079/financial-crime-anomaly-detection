export const MAX_ROWS=5000, MAX_BYTES=5*1024*1024;
export function parseCSV(text){
  if(typeof text!=='string'||new TextEncoder().encode(text).length>MAX_BYTES)throw Error('CSV must be at most 5 MB.');
  const rows=[];let row=[],field='',mode=0;
  const cell=()=>{if(field.length>100)throw Error('CSV cells must be at most 100 characters.');row.push(field);field='';mode=0;if(row.length>7)throw Error('CSV has too many columns.');};
  const line=()=>{cell();if(row.some(v=>v!==''))rows.push(row);row=[];if(rows.length>MAX_ROWS+1)throw Error('CSV must contain at most 5,000 data rows.');};
  text=text.replace(/^\uFEFF/,'');
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(mode===1){if(c==='"'){if(text[i+1]==='"'){field+='"';i++;}else mode=2;}else field+=c;}
    else if(c===',')cell();
    else if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;line();}
    else if(c==='"'&&field===''&&mode===0)mode=1;
    else {if(mode===2||c==='"')throw Error('Malformed CSV quoting.');field+=c;}
    if(field.length>100)throw Error('CSV cells must be at most 100 characters.');
  }
  if(mode===1)throw Error('CSV contains an unclosed quote.');
  if(field!==''||row.length||mode===2)line();
  const header=rows.shift()??[],required=['id','timestamp','sender','receiver','amount','currency'];
  if(new Set(header).size!==header.length||required.some(x=>!header.includes(x))||header.some(x=>![...required,'label'].includes(x)))throw Error('Use unique columns: id,timestamp,sender,receiver,amount,currency; optional label.');
  if(!rows.length)throw Error('CSV has no transactions.');
  const result=rows.map((cells,i)=>{
    if(cells.length!==header.length)throw Error(`Row ${i+2} has the wrong number of columns.`);
    const obj=Object.fromEntries(header.map((h,k)=>[h,cells[k]]));
    if(!/^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/.test(obj.amount))throw Error(`Row ${i+2}: amount must be a positive decimal with at most two decimal places.`);
    obj.amount=Number(obj.amount);
    if('label' in obj){if(obj.label==='')delete obj.label;else if(obj.label==='0'||obj.label==='1')obj.label=Number(obj.label);else throw Error(`Row ${i+2}: optional label must be 0, 1, or blank.`);}
    return obj;
  });
  return result;
}
export function rankScores(records,scores,budget){
  if(records.length!==scores.length||!records.length||scores.some(s=>!Number.isFinite(s)||s<0||s>1)||!Number.isFinite(budget)||budget<1||budget>10)throw Error('Invalid ranking inputs.');
  const ranked=records.map((r,i)=>({record:r,index:i,score:scores[i]})).sort((a,b)=>b.score-a.score||a.index-b.index);
  const k=Math.ceil(records.length*budget/100),alerts=new Set(ranked.slice(0,k).map(x=>x.index));
  return {ranked,k,alerts};
}
export function labelledMetrics(records,alerts,labelsUsable=true){
  if(!labelsUsable||records.some(r=>r.label!==0&&r.label!==1))return {precision:null,recall:null};
  const positives=records.filter(r=>r.label===1).length;
  const tp=[...alerts].filter(i=>records[i].label===1).length;
  return {precision:alerts.size?tp/alerts.size:null,recall:positives?tp/positives:null};
}
