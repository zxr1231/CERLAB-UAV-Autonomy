import math,unittest
from i3_segment_attribution import labeled_samples,spearman,sign,point_segment_distance,components6
class SegmentAttributionTests(unittest.TestCase):
 def test_candidate_and_reference_windows_include_exit_rotation(self):
  ref,rl=labeled_samples([[0,0,0],[1,0,0],[1,1,0]],0,math.pi/2,0,False,1,.2)
  cand,cl=labeled_samples([[0,0,0],[.5,.5,0],[1,0,0],[1,1,0]],0,math.pi/2,0,True,1,.2)
  self.assertIn('replaced_edge',rl);self.assertIn('inserted_incoming',cl);self.assertIn('inserted_outgoing',cl)
  self.assertIn('changed_exit',rl);self.assertIn('changed_exit',cl)
  self.assertEqual('unchanged_suffix',rl[-1]);self.assertEqual('unchanged_suffix',cl[-1])
 def test_last_edge_terminal_rotation_is_changed(self):
  _,labels=labeled_samples([[0,0,0],[1,0,0]],0,math.pi/2,0,False,1,.2)
  self.assertEqual('changed_exit',labels[-1])
 def test_rank_ties_and_constant(self):
  self.assertAlmostEqual(1.,spearman([1,2,2,3],[4,5,5,6]))
  self.assertAlmostEqual(-1.,spearman([1,2,3],[3,2,1]));self.assertIsNone(spearman([1,1],[2,3]))
 def test_sign_tolerance(self):self.assertEqual([0,0,1,-1],[sign(x) for x in [0,1e-10,2e-9,-2e-9]])
 def test_distance_and_components(self):
  self.assertAlmostEqual(1.,point_segment_distance([.5,1,0],[0,0,0],[1,0,0]))
  self.assertEqual([3,1],components6({0,1,2,7},[2,2,2]))
if __name__=='__main__':unittest.main()
