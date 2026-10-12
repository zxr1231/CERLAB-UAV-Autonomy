import unittest
from check_i2_held_out import concordance,decision,model_summary
class GateTest(unittest.TestCase):
 def record(self,stage,actual,pred):
  return {'stage':stage,'actual_count':actual,'actual_per_meter':actual,'actual_per_second':actual,'legacy':{'predicted_count':pred,'predicted_per_meter':pred,'predicted_per_second':pred,'jaccard':.5}}
 def test_global_stage_trend_does_not_hide_reversed_within_stage_order(self):
  r=[self.record(s,k*100+i,k*100+3-i) for k,s in enumerate(['early','middle','late']) for i in range(4)]
  summary=model_summary(r,'legacy');self.assertGreater(summary['per_meter_spearman'],.3);self.assertEqual(0,summary['concordance']);self.assertEqual(18,summary['orderable_pair_count'])
 def test_actual_ties_ignored_predicted_ties_half_empty_actual_retained(self):
  r=[self.record('early',0,1),self.record('early',0,1),self.record('early',1,1)]
  self.assertEqual({'orderable_pair_count':2,'concordance':.5},concordance(r,'legacy'));self.assertEqual(2,model_summary(r,'legacy')['zero_actual_count'])
 def test_insufficient_and_failed_gates_never_pass(self):
  p={'minimum_valid':8,'minimum_per_third':2,'minimum_spearman_per_meter':.3,'minimum_orderable_pairs':9,'minimum_within_third_concordance':.6,'minimum_median_jaccard':.25}
  summary={'count':12,'per_meter_spearman':.8,'orderable_pair_count':18,'concordance':0,'median_jaccard':.5}
  self.assertEqual('FAIL',decision(summary,dict.fromkeys(['early','middle','late'],4),p,[])['status'])
  summary['count']=7;self.assertEqual('INCONCLUSIVE',decision(summary,dict.fromkeys(['early','middle','late'],4),p,[])['status'])
if __name__=='__main__':unittest.main()
