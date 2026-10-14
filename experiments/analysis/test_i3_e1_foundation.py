import unittest
from i3_e1_foundation import choices,decision,MODES
class FoundationTests(unittest.TestCase):
 def test_tie_and_reference_tolerance(self):
  p={'records':[{'u':2,'v':3,'e':0,'motion':{'time':2.,'length':1.}},{'u':4,'v':5,'e':0,'motion':{'time':3.,'length':1.}}]}
  r=[{'record_id':0,'new':1,'utility':5.},{'record_id':1,'new':2,'utility':5.}]
  c=choices(p,r,10,2);self.assertEqual(0,c[MODES[2]]['extra']);self.assertIsNone(c[MODES[2]]['final']);self.assertEqual(1,c[MODES[1]]['extra'])
 def test_zero_gain_and_empty_no_padding(self):
  self.assertTrue(all(x['extra'] is None for x in choices({'records':[]},[],0,2).values()))
  with self.assertRaises(ValueError):choices({},[],0,0)
 def test_gate_not_novelty(self):
  states=[{'sequence':i,'status':'COMPLETE','pool_size':1,'truncated':False,'engineering_parity':True,'choices':{MODES[2]:{'final':0 if i<2 else None}}} for i in range(5)]
  q=decision(states);self.assertEqual('FOUNDATION_PASS_COST_STUDY_PENDING',q['decision']);self.assertFalse(q['guided_generation_admitted']);self.assertFalse(q['timing_admitted'])
  states[0]['choices'][MODES[2]]['final']=None;self.assertEqual('LIMITED_POOL_VALUE_FAIL',decision(states)['decision'])
if __name__=='__main__':unittest.main()
