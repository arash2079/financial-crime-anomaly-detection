import {buildFeatures,scoreRow} from './inference.mjs';
self.onmessage=({data})=>{
  try{
    if(data.records.length>5000)throw Error('Limit is 5,000 records.');
    const features=buildFeatures(data.records),model=data.models.models[data.model];
    if(!model)throw Error('Unknown model.');
    const scores=features.map(f=>scoreRow(f,model));
    self.postMessage({scores,features});
  }catch(e){self.postMessage({error:e.message||'Inference failed.'});}
};
