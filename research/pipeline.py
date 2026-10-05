"""Reproducible synthetic AML research prototype; no real banking data."""
from pathlib import Path
from collections import defaultdict, deque
import hashlib, json, platform, inspect
import numpy as np
import pandas as pd
import scipy, sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'artifacts'
SEED = 2079
FEATURES = ['log_amount','log_sender_out_count_24h','log_sender_out_total_24h',
 'log_receiver_in_count_24h','log_receiver_in_total_24h',
 'log_sender_in_count_24h','log_sender_in_total_24h',
 'log_sender_unique_receivers_24h','amount_to_sender_mean_24h',
 'sender_in_to_out_ratio_24h','log_seconds_since_sender_in']

def simulate(seed=SEED, days=60, daily=500):
    rng = np.random.default_rng(seed)
    origin = 1767225600  # 2026-01-01 UTC
    account_count = 240
    account_scales = rng.lognormal(5.3, .65, account_count)
    rows, episodes = [], []
    def add(t, s, r, amount, label):
        if s == r: r = (r + 1) % account_count
        rows.append((round(t, 0), f'A{s:03d}', f'A{r:03d}', round(float(max(1, amount)), 2), int(label)))
    for day in range(days):
        base = origin + day * 86400
        for _ in range(daily):
            s, r = map(int, rng.integers(0, account_count, 2))
            amount = rng.lognormal(np.log(account_scales[s]), 1.15)
            add(base + int(rng.integers(0, 86400)), s, r, amount, 0)
        # Legitimate high-volume hubs, payroll and rapid reimbursements overlap with alerts.
        for episode in range(5):
            center = int(rng.integers(account_count))
            start = base + int(rng.integers(0, 82000))
            partners = rng.choice(account_count, 10, replace=False)
            for k, partner in enumerate(partners):
                add(start + k * int(rng.integers(15, 200)), center, int(partner), rng.lognormal(6.3, .7), 0)
                if episode % 2 == 0:
                    add(start + k * 100 + 600, int(partner), center, rng.lognormal(5.7, .7), 0)
        for _ in range(6):
            start = base + int(rng.integers(0, 79000))
            actors = list(map(int, rng.choice(account_count, 8, replace=False)))
            hub = actors[0]
            typology = int(rng.integers(3))
            positions = []
            if typology == 0:
                total = 0
                for k, source in enumerate(actors[1:5]):
                    value = rng.lognormal(5.8, 1.1); total += value
                    positions.append(len(rows)); add(start+k*120, source, hub, value, 1)
                for k, target in enumerate(actors[5:]):
                    positions.append(len(rows)); add(start+700+k*90, hub, target, total*rng.uniform(.22,.36), 1)
            elif typology == 1:
                value = rng.lognormal(6.2, 1.0)
                for k in range(7):
                    positions.append(len(rows)); add(start+k*int(rng.integers(30,220)), actors[k], actors[(k+1)%7], value*rng.uniform(.8,1.2), 1)
            else:
                for k, target in enumerate(actors[1:]):
                    positions.append(len(rows)); add(start+k*60, hub, target, rng.lognormal(5.8,.9), 1)
            episodes.append({'day':day,'kind':['fan_in_pass_through','cycle','fan_out'][typology], 'source_positions':positions})
    # Timestamp sort stable; IDs are generated after sorting and are never model inputs.
    rows.sort(key=lambda x:x[0])
    records = [{'id':f'T{i:06d}', 'timestamp':pd.Timestamp(t,unit='s',tz='UTC').isoformat().replace('+00:00','Z'),
                'sender':s,'receiver':r,'amount':v,'currency':'CAD','label':y}
               for i,(t,s,r,v,y) in enumerate(rows)]
    return records, episodes

def causal_features(records):
    """Input sorted UTC timestamps. Prune older than 24h, retaining t-24h exactly.
    Score a whole equal-timestamp group before adding any member to history.
    IDs/labels/currency/account strings are never numerical predictors.
    """
    times = [pd.Timestamp(r['timestamp']).timestamp() for r in records]
    if any(not np.isfinite(t) for t in times) or any(a>b for a,b in zip(times,times[1:])):
        raise ValueError('Records must have valid chronological timestamps.')
    if any(r['currency']!='CAD' or not np.isfinite(r['amount']) or r['amount']<=0 or r['amount']>1e9 or round(r['amount'],2)!=r['amount'] for r in records):
        raise ValueError('Positive finite CAD amounts with at most two decimals, up to 1 billion, are required.')
    incoming, outgoing = defaultdict(deque), defaultdict(deque)
    X=[]; i=0
    def active(bucket, account, t):
        q=bucket[account]
        while q and q[0][0] < t-86400: q.popleft()
        return q
    while i<len(records):
        t=times[i]; j=i
        while j<len(records) and times[j]==t: j+=1
        for row in records[i:j]:
            amount=row['amount']; so=active(outgoing,row['sender'],t)
            si=active(incoming,row['sender'],t); ri=active(incoming,row['receiver'],t)
            # Amount histories are exact integer cents; only final features use dollars.
            sout=sum(x[1] for x in so)/100; sin=sum(x[1] for x in si)/100; rin=sum(x[1] for x in ri)/100
            mean=sout/len(so) if so else 0
            elapsed=min(86400,t-si[-1][0]) if si else 86400
            X.append([np.log1p(amount), np.log1p(len(so)), np.log1p(sout),
             np.log1p(len(ri)), np.log1p(rin), np.log1p(len(si)), np.log1p(sin),
             np.log1p(len({x[2] for x in so})), min(20,amount/(mean+1)),
             min(20,sin/(sout+amount+1)),np.log1p(elapsed)])
        for row in records[i:j]:
            cents=int(round(row['amount']*100))
            outgoing[row['sender']].append((t,cents,row['receiver']))
            incoming[row['receiver']].append((t,cents,row['sender']))
        i=j
    return np.array(X,dtype=float)

def evaluate(y, scores, ids):
    if len(y)==0 or set(np.unique(y))!={0,1}:
        raise ValueError('Evaluation requires a non-empty window containing both labels 0 and 1.')
    result={'averagePrecision':float(average_precision_score(y,scores)),
      'rocAuc':float(roc_auc_score(y,scores)), 'rows':len(y), 'positives':int(sum(y)), 'budgets':[]}
    # Stable sorting means ties preserve chronological row order; number reviewed is ceil(n*budget).
    order=np.argsort(-scores,kind='stable')
    for budget in [.01,.05,.1]:
        count=int(np.ceil(len(y)*budget)); tp=int(sum(y[order[:count]]))
        result['budgets'].append({'fraction':budget,'reviewed':count,'truePositives':tp,
           'precision':tp/count,'recall':tp/int(sum(y))})
    return result

def export_lr(model, scaler):
    return {'type':'logistic','mean':scaler.mean_.tolist(),'scale':scaler.scale_.tolist(),
     'coefficients':model.coef_[0].tolist(),'intercept':float(model.intercept_[0])}

def export_rf(model):
    trees=[]
    for est in model.estimators_:
        t=est.tree_; values=t.value[:,0,:]
        probabilities=values[:,1]/values.sum(axis=1)
        trees.append({'left':t.children_left.tolist(),'right':t.children_right.tolist(),
            'feature':t.feature.tolist(),'threshold':t.threshold.tolist(),'probability':probabilities.tolist()})
    return {'type':'forest','trees':trees,'inputDtype':'float32'}

def run():
    OUT.mkdir(exist_ok=True)
    records, episodes=simulate()
    X=causal_features(records); y=np.array([r['label'] for r in records])
    ts=pd.to_datetime([r['timestamp'] for r in records],utc=True)
    origin=ts[0].normalize()
    masks={'train':np.asarray(ts<origin+pd.Timedelta(days=36)),
        'validation':np.asarray((ts>=origin+pd.Timedelta(days=36))&(ts<origin+pd.Timedelta(days=48))),
        'test':np.asarray(ts>=origin+pd.Timedelta(days=48))}
    models={}; metrics={}; finalRf=None
    for variant, cols in [('tabular',[0]),('historical',list(range(len(FEATURES))))]:
        scaler=StandardScaler().fit(X[masks['train']][:,cols])
        lr=LogisticRegression(class_weight='balanced',max_iter=500,random_state=SEED).fit(scaler.transform(X[masks['train']][:,cols]),y[masks['train']])
        rf=RandomForestClassifier(n_estimators=32,max_depth=8,min_samples_leaf=12,class_weight='balanced',random_state=SEED,n_jobs=2).fit(X[masks['train']][:,cols],y[masks['train']])
        iso=IsolationForest(n_estimators=32,max_samples=256,random_state=SEED,n_jobs=2).fit(X[masks['train']][:,cols])
        for name, model in [('logistic',lr),('forest',rf),('isolation',iso)]:
            key=f'{variant}_{name}'; metrics[key]={}
            for split in ['validation','test']:
                xx=X[masks[split]][:,cols]
                score=lr.predict_proba(scaler.transform(xx))[:,1] if name=='logistic' else rf.predict_proba(xx)[:,1] if name=='forest' else -iso.score_samples(xx)
                metrics[key][split]=evaluate(y[masks[split]],score,None)
            if variant=='historical' and name in ['logistic','forest']:
                models[name]=export_lr(lr,scaler) if name=='logistic' else export_rf(rf)
                if name=='forest': finalRf=rf
    metrics['amount_rule']={split:evaluate(y[masks[split]],X[masks[split],0],None) for split in ['validation','test']}
    raw=json.dumps(records,separators=(',',':')).encode()
    metadata={'seed':SEED,'dataset':'Original synthetic transactions; not IBM AML-Data',
      'rows':len(records),'positives':int(y.sum()),'sha256':hashlib.sha256(raw).hexdigest(),
      'start':records[0]['timestamp'],'end':records[-1]['timestamp'],
      'splits':{s:{'rows':int(m.sum()),'positives':int(y[m].sum()),'start':records[np.flatnonzero(m)[0]]['timestamp'],'end':records[np.flatnonzero(m)[-1]]['timestamp']} for s,m in masks.items()},
      'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'scikit-learn':sklearn.__version__},
      'functionHashes':{f.__name__:hashlib.sha256(inspect.getsource(f).encode()).hexdigest() for f in [simulate,causal_features]},
      'trainingPolicy':'Fit train only; fixed model settings; validation report only. Test untouched by tuning. Historical context continues across chronological splits.',
      'limitations':['Synthetic labels encode generator patterns, not confirmed criminality.','No operational or real-world effectiveness claim.','Benign hubs/payroll and anomalous amounts overlap, but simulator artifacts remain.','Isolation Forest anomaly rank is not calibrated probability.','Browser LR/RF probabilities are synthetic-label scores, not probability of financial crime.','No customer/bank/TD data used.'],
      'externalDatasetStatus':'IBM AML-Data not downloaded or evaluated; no external-data results claimed.'}
    (OUT/'models.json').write_text(json.dumps({'schemaVersion':1,'features':FEATURES,'windowSeconds':86400,'models':models},separators=(',',':')))
    demo,_=simulate(seed=SEED+1,days=2,daily=400)
    demoX=causal_features(demo)
    modelLR=models['logistic']
    referenceScores=1/(1+np.exp(-(((demoX-np.array(modelLR['mean']))/np.array(modelLR['scale']))@np.array(modelLR['coefficients'])+modelLR['intercept'])))
    demoChecksum=hashlib.sha256(json.dumps(demo,separators=(',',':')).encode()).hexdigest()
    (OUT/'demo.json').write_text(json.dumps({'metadata':{'seed':SEED+1,'kind':'self-contained synthetic scenario; separate from benchmark','rows':len(demo),'sha256':demoChecksum,'history':'Starts from empty history; includes all events for these 2 days.'},'records':demo},separators=(',',':')))
    forestScores=finalRf.predict_proba(demoX)[:,1]
    fixture={'recordIndices':list(range(len(demo))),'features':demoX.tolist(),
        'logisticScores':referenceScores.tolist(),'forestScores':forestScores.tolist()}
    (OUT/'parity-fixture.json').write_text(json.dumps(fixture,separators=(',',':')))
    exampleIndex=int(np.argmax(forestScores))
    metadata['replayExample']={'demoRecordIndex':exampleIndex,'record':demo[exampleIndex],
        'features':demoX[exampleIndex].tolist(),'logisticScore':float(referenceScores[exampleIndex]),'forestScore':float(forestScores[exampleIndex]),
        'replay':'Load full demo.json, build all chronological features, select demoRecordIndex, score using models.json.'}
    (OUT/'metrics.json').write_text(json.dumps({'metadata':metadata,'results':metrics},indent=2))
    print(json.dumps({'rows':len(records),'demoRows':len(demo),'test':{k:v['test'] for k,v in metrics.items()}},indent=2))

if __name__=='__main__': run()
