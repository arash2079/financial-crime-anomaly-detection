import unittest
import numpy as np
from pipeline import causal_features, simulate, evaluate

def row(id,t,s,r,a,label=0):
    return {'id':id,'timestamp':f'2026-01-01T{t}Z','sender':s,'receiver':r,'amount':a,'currency':'CAD','label':label}

class CausalFeaturesTests(unittest.TestCase):
    def test_same_timestamp_not_visible(self):
        records=[row('1','00:00:00','A','B',100),row('2','00:00:00','A','C',100),row('3','00:01:00','A','D',100)]
        X=causal_features(records)
        self.assertEqual(X[0,1],0);self.assertEqual(X[1,1],0)
        self.assertAlmostEqual(X[2,1],np.log1p(2))
    def test_future_does_not_change_past(self):
        records,_=simulate(3,days=1,daily=30)
        prefix=records[:50]
        np.testing.assert_array_equal(causal_features(prefix),causal_features(records)[:50])
    def test_labels_and_ids_not_predictors(self):
        records,_=simulate(4,days=1,daily=20)
        edited=[dict(r,label=1-r['label'],id='changed'+r['id']) for r in records]
        np.testing.assert_array_equal(causal_features(records),causal_features(edited))
    def test_account_rename_invariant(self):
        records,_=simulate(5,days=1,daily=20)
        edited=[dict(r,sender='prefix'+r['sender'],receiver='prefix'+r['receiver']) for r in records]
        np.testing.assert_array_equal(causal_features(records),causal_features(edited))
    def test_window_boundary(self):
        records=[row('1','00:00:00','A','B',100),dict(row('2','00:00:00','A','C',100),timestamp='2026-01-02T00:00:00Z'),dict(row('3','00:00:01','A','D',100),timestamp='2026-01-02T00:00:01Z')]
        X=causal_features(records)
        self.assertAlmostEqual(X[1,1],np.log1p(1));self.assertAlmostEqual(X[2,1],np.log1p(1))
    def test_seed_determinism(self):
        self.assertEqual(simulate(9,1,30)[0],simulate(9,1,30)[0])
    def test_equivalent_timestamp_groups(self):
        records=[row('1','00:00:00','A','B',100),dict(row('2','00:00:00','A','C',100),timestamp='2026-01-01T00:00:00+00:00')]
        self.assertEqual(causal_features(records)[1,1],0)
    def test_unsorted_rejected(self):
        with self.assertRaises(ValueError):causal_features([row('1','01:00:00','A','B',10),row('2','00:00:00','A','C',10)])
    def test_single_class_evaluation_rejected(self):
        for y in [np.array([]),np.zeros(3),np.ones(3)]:
            with self.assertRaises(ValueError):evaluate(y,y,None)
    def test_cent_contract(self):
        with self.assertRaises(ValueError):causal_features([row('1','00:00:00','A','B',.001)])
    def test_extreme_expiry_retains_one_cent(self):
        import pandas as pd
        def extreme(i,seconds,amount):
            return {'id':str(i),'timestamp':(pd.Timestamp('2026-01-01',tz='UTC')+pd.Timedelta(seconds=seconds)).isoformat().replace('+00:00','Z'),'sender':'A','receiver':'B','amount':amount,'currency':'CAD'}
        records=[extreme(i,i,900000000.01) for i in range(9999)]+[extreme(9999,10001,.01),extreme(10000,96400,.02)]
        self.assertEqual(causal_features(records)[-1,2],np.log1p(.01))

if __name__=='__main__':unittest.main()
