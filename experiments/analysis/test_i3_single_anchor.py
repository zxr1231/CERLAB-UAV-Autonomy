import unittest,copy
from i3_single_anchor import choose,route_effect,gates
class SingleAnchorTests(unittest.TestCase):
 def proxy(self,i,n,t):return dict(record_id=i,anchor=i,edge=0,time=t,length=5.,new_voxels=n)
 def test_residual_can_differ_from_naive_without_oracle(self):
  rows=[self.proxy(1,50,6),self.proxy(2,60,8)]
  self.assertEqual({'geometry':1,'naive_marginal':2,'residual_cost':1},choose(rows,100,5))
  rows[0]['oracle_gain']=0;rows[1]['oracle_gain']=1000000
  self.assertEqual(1,choose(rows,100,5)['residual_cost'])
 def test_empty_pool_and_negative_proxy_select_without_padding(self):
  self.assertTrue(all(v is None for v in choose([],0,5).values()))
  self.assertEqual(2,choose([self.proxy(2,0,8)],100,5)['residual_cost'])
 def test_exact_ties_stable_under_input_order(self):
  a,b=self.proxy(1,20,6),self.proxy(2,20,6)
  self.assertEqual(choose([a,b],100,5),choose([b,a],100,5))
 def test_net_loss_not_hidden_by_new_count(self):
  e=route_effect([1,2,3],[3,4,5],5,6,2)
  self.assertEqual(2,e['added']);self.assertEqual(2,e['lost']);self.assertLess(e['net_value'],0)
  self.assertEqual('reference',e['final_choice']);self.assertLess(e['raw_relative_rate'],0);self.assertEqual(0,e['effective_relative_rate'])
 def test_net_value_utility_identity_and_independent_history(self):
  args=([1,2],[2,3,4],5,6,2);a=route_effect(*args);route_effect([999],[1000],2,4,0);b=route_effect(*args)
  self.assertEqual(a,b);self.assertAlmostEqual(a['net_value']/6,a['utility']-a['reference_utility'])
 def test_zero_reference_cannot_make_relative_gate_pass(self):
  self.assertIsNone(route_effect([],[],5,5,0)['effective_relative_rate'])
 def test_gates_keep_five_denominator_and_require_distinct_signal(self):
  states=[]
  for i in range(5):
   e={'effective_utility':1.,'effective_relative_rate':0.}
   states.append({'status':'COMPLETE','sequence':i,'reference_utility':1.,'evaluated':[], 'selectors':{m:copy.copy(e) for m in ['geometry','naive_marginal','residual_cost']}})
  self.assertEqual('NO_USEFUL_SUPPLY_IN_THIS_SCOPE',gates(states)['decision'])
  for s in states[:2]:
   s['evaluated']=[{'utility':2.}]
   for m in ['naive_marginal','residual_cost']:s['selectors'][m]={'effective_utility':2.,'effective_relative_rate':1.}
  self.assertEqual('NO_DISTINCT_METHOD_SIGNAL',gates(states)['decision'])
  self.assertEqual('ENGINEERING_FAIL',gates(states[:4])['decision'])
if __name__=='__main__':unittest.main()
