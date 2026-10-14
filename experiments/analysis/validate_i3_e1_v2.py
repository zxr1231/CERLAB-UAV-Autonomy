#!/usr/bin/env python3
"""Read-only reconstruction of completed V2 E1 artifacts; no visibility queries."""
import argparse,json,hashlib,math,struct
from pathlib import Path
from i3_e1_foundation import choices,decision
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fp(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('results',type=Path);a.add_argument('--output',type=Path);args=a.parse_args();root=args.results;repo=Path(__file__).resolve().parents[2]
 q=json.loads((repo/'experiments/i3/I3_02E_PROTOCOL_V2.json').read_text());reg=json.loads((repo/'experiments/i3/I3_02E_INPUTS_V2.json').read_text());summary=json.loads((root/'summary.json').read_text());batch=json.loads((root/'batch_state.json').read_text());assert summary['identity']==batch['identity'] and batch['status']=='COMPLETE'
 assert summary['identity']['protocol_sha256']==sha(repo/'experiments/i3/I3_02E_PROTOCOL_V2.json');assert summary['identity']['registry_sha256']==sha(repo/'experiments/i3/I3_02E_INPUTS_V2.json')
 rows_count=0;resources=[]
 for c in reg['cases']:
  seq=c['sequence'];entry=next(s for s in batch['states'] if s['sequence']==seq);prefix='s%03d'%seq
  assert all(sha(Path(c['snapshot_directory'])/n)==h for n,h in c['snapshot_sha256'].items())
  assert all(sha(Path(reg['source_root'])/n)==h for n,h in c['source_sha256'].items());assert fp(c['context'])==c['context_fingerprint']
  pool=json.loads((root/(prefix+'_pool.json')).read_text())
  if seq==13:
   assert entry['status']=='SKIPPED_NEGATIVE_CONTROL' and pool['camera_calls']==pool['pairs_enumerated']==0;continue
  s=json.loads((root/('state_%06d.json'%seq)).read_text());assert sha(root/('state_%06d.json'%seq))==entry['state_sha256'];assert s==next(x for x in summary['states'] if x['sequence']==seq)
  selectedfile=root/(prefix+'_selection.json');selected=json.loads(selectedfile.read_text());assert sha(selectedfile)==entry['selection_sha256'];assert sha(root/(prefix+'_compose.json'))==selected['compose_sha256']
  comp=json.loads((root/(prefix+'_compose.json')).read_text());oracle=json.loads((root/(prefix+'_oracle.json')).read_text());oref=oracle['rows'][0]['metrics'];assert comp['reference']==oref
  assert choices(pool,comp['rows'],oref['unique'],s['reference_time'])==selected['choices']==s['choices']
  rset=set(oref['addresses']);assert sum(oref['marginal'])==oref['unique']==len(rset);assert oref['raw']>=oref['unique']
  o={x['record_id']:x['metrics'] for x in oracle['rows'][1:]}
  assert [x['record_id'] for x in comp['rows']]==pool['pool'];assert not pool['truncated'] and len(pool['records'])==pool['possible_pairs']
  req=json.loads(Path(c['request_file']).read_text());edges={tuple(x) for x in req['edges']};count=(len(req['reference'])-1)*sum(1 for u,v in edges if u and v and u!=v);assert count==pool['possible_pairs']
  n=len(pool['ordered']);assert pool['pool']==(pool['ordered'] if n<=5 else [pool['ordered'][j*(n-1)//4] for j in range(5)])
  for x in comp['rows']:
   rid=x['record_id'];r=pool['records'][rid];m=x['metrics'];assert m==o[rid];assert not r['reasons'] and (r['u'],r['v']) in edges
   assert r['motion']['length']<=1.25*pool['reference_motion']['length'] and r['motion']['time']<=1.25*pool['reference_motion']['time'] and r['motion']['yaw']<=pool['reference_motion']['yaw']+q['motion']['extra_yaw_max']
   vis=set(m['addresses']);assert len(vis)==m['unique']==sum(m['marginal']) and m['raw']>=m['unique']
   assert x['new']==len(vis-rset) and x['lost']==len(rset-vis);assert x['utility']==m['unique']/x['time'];rows_count+=1
  assert comp['visibility_requested_peak_bytes']<=256*1024*1024 and not comp['allocation_limit_rejected']
  # Model logical payload only, not vector capacity or RSS; derived from locked source.
  with open(Path(c['snapshot_directory'])/'map.bin','rb') as f:
   f.read(8+4+8+8+24+24);dims=struct.unpack('<3i',f.read(12))
  camera=c['context']['camera'];rays=len(range(camera['filter_margin'],camera['image_rows']-camera['filter_margin'],camera['evaluation_pixel_skip']))*len(range(camera['filter_margin'],camera['image_cols']-camera['filter_margin'],camera['evaluation_pixel_skip']))
  resources.append({'sequence':seq,'model_logical_payload_bytes':math.prod(dims)+rays*24,'model_storage_capacity_measured':False,'rss_measured':False,'input_map_bytes_reported':comp['input_map_bytes'],'tracked_visibility_peak_bytes':comp['visibility_requested_peak_bytes']})
 reconstructed=decision(summary['states']);assert all(summary[k]==v for k,v in reconstructed.items())
 validation={'schema':'i3-e1-read-only-validation-v2','status':'PASS','states':5,'negative_control':13,'routes_checked':rows_count,'source_hashes':'UNCHANGED','reference_and_full_route_metrics':'EXACT','selection_checkpoints':'SHA256_VERIFIED','decision_reconstructed':reconstructed,'resources':resources,'resource_limits':['tracked C++ requested capacities include allocator headers, not malloc arena slack','model payload calculated from source; allocated capacity and process peak RSS not collected in primary batch','one-shot component/process times are not E2 or fair deployed-speed evidence']}
 if args.output:args.output.write_text(json.dumps(validation,indent=2)+'\n')
 print(json.dumps(validation,indent=2))
if __name__=='__main__':main()
