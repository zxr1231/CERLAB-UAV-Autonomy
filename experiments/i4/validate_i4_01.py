#!/usr/bin/env python3
"""Independent frozen-source/parity checks; no modification of any recorded run."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 inputs,results=map(Path,sys.argv[1:3]);manifest=json.loads((inputs/'manifest.json').read_text())
 for f,h in manifest['protected'].items():assert sha(Path(f))==h,f
 rows={}
 for p in results.glob('r0_s*_m0.jsonl'):
  for line in p.read_text().splitlines():
   r=json.loads(line);rows[r['sequence']]=r
 oldroot=Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-00-SAME-SNAPSHOT-V1');old_checks=0
 for seq in [1,13,14,26,27,38]:
  old=json.loads((oldroot/('result_%06d.json'%seq)).read_text())['repeats'][0]['routes']
  new=rows[seq]['routes'];assert len(old)==len(new)
  for a,b in zip(old,new):
   assert a['raw_gain']==b['raw'] and a['unique_gain']==b['unique'] and a['marginals']==b['marginal'] and a['sample_count']==b['sample_count'],(seq,a['id'])
   old_checks+=1
 test_rows=[];prior_failures=[]
 for p in sorted(Path('/tmp').glob('i4_01_*.xml')):
  root=ET.parse(p).getroot();row={'file':p.name,'tests':int(root.get('tests','0')),'failures':int(root.get('failures','0')),'errors':int(root.get('errors','0'))}
  (prior_failures if p.name.endswith('_pre_sync_failure.xml') else test_rows).append(row)
 assert all(r['failures']==r['errors']==0 for r in test_rows)
 out={'protected_files_unchanged':len(manifest['protected']),'old_frozen_full_oracle_route_parity':old_checks,'cpp_tests':test_rows,'retained_prior_failures':prior_failures,'tests_total':sum(r['tests'] for r in test_rows),'all_current_cpp_tests_passed':True,'old_reference_parity_compares_counts_marginals_not_unavailable_old_addresses':True}
 (results/'validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
