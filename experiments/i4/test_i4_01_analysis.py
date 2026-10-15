import contextlib,io,json,tempfile,unittest
from pathlib import Path
from summarize_i4_01 import summarize,percentile

class AnalysisTests(unittest.TestCase):
 def fixture(self,root,dependency_ms=3):
  for repeat in range(3):
   for segment,(lo,hi) in enumerate([(1,13),(14,26),(27,38)]):
    for mode,cost in enumerate([10,5,4,dependency_ms]):
     lines=[]
     for seq in range(lo,hi+1):
      row={k:0 for k in ['charged_cache_bytes','tracked_working_peak_bytes','process_peak_rss_kib','recomputed_poses','reused_poses','membership_updates','propagated_memberships','evictions']}
      row.update(sequence=seq,total_ms=cost,winner=0,routes=[{'addresses':[10],'raw':1,'unique':1,'marginal':[1]}],allocation_limit_rejected=False)
      lines.append(json.dumps(row))
     (root/f'r{repeat}_s{segment}_m{mode}.jsonl').write_text('\n'.join(lines)+'\n')
 def result(self,root):
  with contextlib.redirect_stdout(io.StringIO()):return summarize(root)
 def test_both_cost_controls_required(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);self.assertEqual('PROTOTYPE_COST_GATE_PASS',self.result(root)['status'])
   self.fixture(root,4.5);self.assertEqual('PROTOTYPE_COST_GATE_FAIL',self.result(root)['status'])
 def test_equal_count_different_address_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);p=root/'r0_s0_m3.jsonl';lines=p.read_text().splitlines();j=json.loads(lines[0]);j['routes'][0]['addresses']=[11];lines[0]=json.dumps(j);p.write_text('\n'.join(lines)+'\n')
   with self.assertRaises(AssertionError):self.result(root)
 def test_missing_record_is_not_silently_excluded(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);(root/'r0_s0_m3.jsonl').unlink()
   with self.assertRaises(AssertionError):self.result(root)
 def test_percentile_is_interpolated(self):self.assertEqual(9.5,percentile([0,10],.95))
if __name__=='__main__':unittest.main()
