import math,unittest
from i3_route_sampling import sample_route
class RouteSamplingTest(unittest.TestCase):
 def test_terminal_rotation_included_and_translation_spacing_bounded(self):
  points=[{'position':[0,0,1],'yaw':0},{'position':[1,0,1],'yaw':math.pi/2}]
  r=sample_route(points,0);self.assertEqual(21,len(r['samples']));self.assertAlmostEqual(1,r['length']);self.assertAlmostEqual(math.pi/2,r['yaw_distance'])
  for a,b in zip(r['samples'],r['samples'][1:]):
   self.assertLessEqual(math.dist(a['position'],b['position']),.25+1e-12);self.assertLessEqual(abs(math.remainder(a['yaw']-b['yaw'],2*math.pi)),.1+1e-12)
 def test_shortest_wrap_and_goal_set_independent(self):
  h=-math.pi+.05;r=sample_route([{'position':[0,0,1],'yaw':h},{'position':[math.cos(h),math.sin(h),1],'yaw':h}],math.pi-.05)
  self.assertAlmostEqual(.1,r['yaw_distance']);self.assertLess(len(r['samples']),10)
 def test_corner_rotation_and_translation_only_are_explicitly_different(self):
  p=[{'position':[0,0,1],'yaw':0},{'position':[1,0,1],'yaw':math.pi/2},{'position':[1,1,1],'yaw':math.pi/2}]
  r=sample_route(p,0);cheap=sample_route(p,0,include_rotations=False)
  self.assertEqual(r['length'],cheap['length']);self.assertEqual(r['yaw_distance'],cheap['yaw_distance']);self.assertGreater(len(r['samples']),len(cheap['samples']))
  self.assertEqual([1,1,1],r['samples'][-1]['position'])
 def test_hover_yaw_and_invalid_inputs(self):
  r=sample_route([{'position':[0,0,1],'yaw':math.pi/2}],0);self.assertEqual(17,len(r['samples']));self.assertEqual(0,r['length'])
  with self.assertRaises(ValueError):sample_route([],0)
  with self.assertRaises(ValueError):sample_route([{'position':[0,float('nan'),1],'yaw':0}],0)
if __name__=='__main__':unittest.main()
