import unittest
from i3_observation_loss import compare_sets,classify
P={'raw_as_final_length_ratio_max':1.25,'raw_as_final_time_ratio_max':1.25,'raw_as_final_additional_yaw_max':1.57,'material_lost_voxels_min':1,'material_loss_ratio_min':.05,'utility_improvement_tolerance':1e-9}
class LossTest(unittest.TestCase):
 def test_equal_counts_do_not_imply_same_observation(self):
  r=compare_sets([1,2],[2,3]);self.assertEqual((1,1,0),(r['lost_count'],r['added_count'],r['net_before_minus_after']));self.assertAlmostEqual(1/3,r['jaccard'])
 def test_empty_before_not_material_loss(self):
  m={'length':1,'time':1,'yaw_distance':0};r=classify([],[],[],m,m,P);self.assertFalse(r['direct_raw_retention_lead']);self.assertEqual(0,r['shortcut_change']['loss_ratio'])
 def test_raw_reference_feasibility_does_not_imply_final_feasibility(self):
  raw={'length':2,'time':2,'yaw_distance':1};ref={'length':1,'time':1,'yaw_distance':0};r=classify([1,2,3],[1],[1],raw,ref,P);self.assertTrue(r['material_predicted_loss']);self.assertTrue(r['raw_utility_improves']);self.assertFalse(r['direct_raw_retention_lead'])
 def test_positive_lead_requires_extra_and_utility(self):
  m={'length':1,'time':1,'yaw_distance':0};self.assertTrue(classify([1,2],[1],[1],m,m,P)['direct_raw_retention_lead']);self.assertFalse(classify([1,2],[1],[1],m,m,P,False)['direct_raw_retention_lead'])
if __name__=='__main__':unittest.main()
