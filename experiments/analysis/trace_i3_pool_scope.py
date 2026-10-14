#!/usr/bin/env python3
"""Read-only trace through already saved pools; never compute new visibility or routes."""
import argparse,json,hashlib
from pathlib import Path
from collections import Counter
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args()
 root=Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-E1-FOUNDATION-V2');old=Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-02A-SINGLE-ANCHOR-V1');source=Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-01B-TWO-STAGE-V1')
 for line in (root/'SHA256SUMS').read_text().splitlines():
  digest,p=line.split('  ',1);assert sha(Path(p))==digest
 states=[];hashes={}
 for seq in [1,14,26,27,38]:
  f=root/f's{seq:03d}_pool.json';hashes[str(f)]=sha(f);p=json.loads(f.read_text());request_file=source/f'request_{seq:06d}.json';hashes[str(request_file)]=sha(request_file);req=json.loads(request_file.read_text());edges={tuple(x) for x in req['edges']}
  sf=old/f'state_{seq:06d}.json';hashes[str(sf)]=sha(sf);s=json.loads(sf.read_text())
  reasons=Counter(reason for row in p['records'] for reason in row['reasons'])
  feasible=[x for x in p['records'] if not set(x['reasons'])-{'edge_insertion_not_best','position_sequence_duplicate'}]
  positives=[]
  for x in s['evaluated']:
   if x['effect']['raw_relative_rate']>0:
    matches=[r for r in p['records'] if r['path']==x['path']]
    positives.append({'old_record_id':x['record_id'],'old_path':x['path'],'old_relative_u':x['effect']['raw_relative_rate'],'existing_nonstart_arcs_along_old_path':[list((u,v)) for u,v in zip(x['path'],x['path'][1:]) if u and v and (u,v) in edges],
                      'identical_e1_path_records':[{'record_id':r['record_id'],'reasons':r['reasons']} for r in matches]})
  states.append({'sequence':seq,'enumerated_pairs':len(p['records']),'motion_safe_before_per_edge_filter':len(feasible),'per_edge_filter_rejections':reasons['edge_insertion_not_best'],'geometry_duplicate_rejections':reasons['position_sequence_duplicate'],'qualified_distinct':len(p['ordered']),'evaluated_small_pool':len(p['pool']),'qualified_not_evaluated':len(p['ordered'])-len(p['pool']), 'known_old_positive_paths':positives})
 result={'schema':'i3-scope-trace-v1','states':states,'source_sha256':hashes,'new_visibility_queries':0,'new_routes_generated':0,'new_simulation':False,'old_e1_decision_unchanged':'LIMITED_POOL_VALUE_FAIL',
         'limits':['unscored candidate values cannot be inferred from geometry','old non-Edge route not representable verbatim does not prove all Edge detours lack value','no causal exploration-performance conclusion']}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(states,indent=2))
if __name__=='__main__':main()
