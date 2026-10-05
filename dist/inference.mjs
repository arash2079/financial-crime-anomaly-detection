// Exact browser/Node implementation of the causal Python feature contract.
export const FEATURE_NAMES = ['log_amount','log_sender_out_count_24h','log_sender_out_total_24h',
 'log_receiver_in_count_24h','log_receiver_in_total_24h','log_sender_in_count_24h',
 'log_sender_in_total_24h','log_sender_unique_receivers_24h','amount_to_sender_mean_24h',
 'sender_in_to_out_ratio_24h','log_seconds_since_sender_in'];

export function validateRecords(records) {
  if (!Array.isArray(records) || !records.length || records.length > 20000) throw new Error('Provide 1–20,000 transaction records.');
  let previous = -Infinity; const ids = new Set();
  for (const r of records) {
    if (!r || typeof r!=='object' || Array.isArray(r)) throw new Error('Every transaction must be an object.');
    const t = Date.parse(r.timestamp);
    const canonical=Number.isFinite(t)?new Date(t).toISOString():'';
    const normalized=typeof r.timestamp==='string'?(/\.\d{3}Z$/.test(r.timestamp)?r.timestamp:r.timestamp.replace(/Z$/,'.000Z')):'';
    if (!Number.isFinite(t) || t < previous || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/.test(r.timestamp) || normalized!==canonical) throw new Error('Timestamps must be valid canonical UTC ISO strings ending in Z, ordered chronologically.');
    if (typeof r.id !== 'string' || !r.id || r.id.length>128 || ids.has(r.id)) throw new Error('Transaction IDs must be unique non-empty strings up to 128 characters.');
    if (typeof r.sender !== 'string' || !r.sender || r.sender.length>128 || typeof r.receiver !== 'string' || !r.receiver || r.receiver.length>128 || r.sender === r.receiver) throw new Error('Sender and receiver must be distinct non-empty account strings up to 128 characters.');
    if (!Number.isFinite(r.amount) || r.amount <= 0 || r.amount > 1e9 || Number(r.amount.toFixed(2))!==r.amount || r.currency !== 'CAD') throw new Error('Amount must be finite, positive, have at most two decimal places, and be at most CAD 1 billion; currency must be CAD.');
    if (r.label !== undefined && r.label !== 0 && r.label !== 1) throw new Error('Optional synthetic label must be 0 or 1.');
    ids.add(r.id); previous=t;
  }
  return records;
}

export function buildFeatures(records) {
  validateRecords(records);
  const incoming=new Map(), outgoing=new Map(), features=[];
  function queue(bucket,account) {
    if(!bucket.has(account))bucket.set(account,{items:[],head:0,total:0,counts:new Map()});
    return bucket.get(account);
  }
  function active(bucket, account, t) {
    const q=queue(bucket,account);
    while(q.head<q.items.length && q.items[q.head][0]<t-86400) {
      const old=q.items[q.head++]; q.total-=old[1];
      const count=q.counts.get(old[2])-1;
      if(count)q.counts.set(old[2],count);else q.counts.delete(old[2]);
    }
    if(q.head===q.items.length){q.items=[];q.head=0;q.total=0;}
    else if(q.head>1024 && q.head>q.items.length/2){q.items=q.items.slice(q.head);q.head=0;}
    return q;
  }
  function append(bucket,account,event) {
    const q=queue(bucket,account);q.items.push(event);q.total+=event[1];
    q.counts.set(event[2],(q.counts.get(event[2])||0)+1);
  }
  const count=q=>q.items.length-q.head;
  let i=0;
  while (i<records.length) {
    const t=Date.parse(records[i].timestamp)/1000; let j=i;
    while(j<records.length && Date.parse(records[j].timestamp)/1000===t) j++;
    for(let k=i;k<j;k++) {
      const r=records[k], so=active(outgoing,r.sender,t), si=active(incoming,r.sender,t), ri=active(incoming,r.receiver,t);
      // Histories aggregate exact cents. 20,000 * CAD 1e9 * 100 < 2^53.
      const sout=so.total/100, sin=si.total/100, rin=ri.total/100, mean=count(so)?sout/count(so):0;
      const elapsed=count(si)?Math.min(86400,t-si.items[si.items.length-1][0]):86400;
      features.push([Math.log1p(r.amount),Math.log1p(count(so)),Math.log1p(sout),
        Math.log1p(count(ri)),Math.log1p(rin),Math.log1p(count(si)),Math.log1p(sin),
        Math.log1p(so.counts.size),Math.min(20,r.amount/(mean+1)),
        Math.min(20,sin/(sout+r.amount+1)),Math.log1p(elapsed)]);
    }
    for(let k=i;k<j;k++) {
      const r=records[k];
      const cents=Math.round(r.amount*100);
      append(outgoing,r.sender,[t,cents,r.receiver]);
      append(incoming,r.receiver,[t,cents,r.sender]);
    }
    i=j;
  }
  return features;
}

export function scoreRow(features, model) {
  if (features.length!==FEATURE_NAMES.length || features.some(x=>!Number.isFinite(x))) throw new Error('Invalid feature vector.');
  if(model.type==='logistic') {
    const z=features.reduce((z,x,i)=>z+(x-model.mean[i])/model.scale[i]*model.coefficients[i],model.intercept);
    return z>=0?1/(1+Math.exp(-z)):Math.exp(z)/(1+Math.exp(z));
  }
  if(model.type==='forest') {
    // sklearn's tree inference explicitly casts input to float32.
    const x=features.map(Math.fround);
    return model.trees.reduce((sum,t)=>{
      let n=0;
      while(t.left[n]!==-1) n=x[t.feature[n]]<=t.threshold[n]?t.left[n]:t.right[n];
      return sum+t.probability[n];
    },0)/model.trees.length;
  }
  throw new Error('Supported model types are logistic and forest.');
}

export function scoreRecords(records, models, modelName='forest') {
  const model=models.models[modelName]; if(!model)throw new Error('Unknown model.');
  return buildFeatures(records).map(x=>scoreRow(x,model));
}

export function logisticContributions(features,model) {
  if(model.type!=='logistic')throw new Error('Exact additive contributions are available only for logistic regression.');
  return features.map((x,i)=>({feature:FEATURE_NAMES[i],value:x,contribution:(x-model.mean[i])/model.scale[i]*model.coefficients[i]}));
}
