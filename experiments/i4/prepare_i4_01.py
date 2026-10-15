#!/usr/bin/env python3
"""Prepare all registered historical candidates, without computing any new gains."""
import hashlib,json,sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'experiments/analysis'))
from i3_route_sampling import sample_route

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
 old=json.loads((REPO/'experiments/i3/I3_03_02_INPUTS.json').read_text())
 source=Path(old['source_run']);events={r['global_sequence']:r['route_controls'] for r in map(json.loads,(source/'route_controls.jsonl').read_text().splitlines())}
 config=json.loads(Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-00-SAME-SNAPSHOT-V1/request_000001.json').read_text())['config']
 protected={str(source/'route_controls.jsonl'):sha(source/'route_controls.jsonl')}
 cases=[]
 for case in old['cases']:
  seq=case['sequence'];folder=Path(case['snapshot'])
  for name,digest in case['snapshot_sha256'].items():
   p=folder/name;assert sha(p)==digest;protected[str(p)]=digest
  p=json.loads((folder/'planner.json').read_text());e=events[seq];assert e['status']=='ready' and not e['fallback']
  c=dict(config);c['planning_min']=p['planning_region']['min'];c['planning_max']=p['planning_region']['max'];routes=[]
  for candidate in sorted(p['candidate_paths'],key=lambda r:r['id']):
   sampled=sample_route(candidate['waypoints'],e['start_yaw'],.25,.1)
   motion=p['motion_model'];t=sampled['length']/motion['velocity']+motion['yaw_penalty_weight']*sampled['yaw_distance']/motion['angular_velocity']
   assert abs(t-candidate['legacy_metrics']['estimated_time'])<1e-8
   routes.append({'id':candidate['id'],'estimated_time':t,'samples':sampled['samples']})
  assert routes
  request=out/('request_%06d.json'%seq);request.write_text(json.dumps({'config':c,'routes':routes})+'\n')
  cases.append({'sequence':seq,'request':str(request),'request_sha256':sha(request),'map':str(folder/'map.bin'),'originally_accepted':case['accepted_at_recording'],'routes':len(routes),'samples':sum(len(r['samples']) for r in routes)})
 for segment,(lo,hi) in enumerate([(1,13),(14,26),(27,38)]):
  (out/('segment_%d.json'%segment)).write_text(json.dumps({'events':[c for c in cases if lo<=c['sequence']<=hi]},indent=2)+'\n')
 manifest={'task':'I4-01','source_run':str(source),'cases':cases,'protected':protected,'protocol_sha256':sha(Path(__file__).with_name('I4_01_PROTOCOL.md')),'limitations':['one historical run, three correlated segments','sparse exported maps, not all sensor-frame updates','all recorded candidate paths, including rejected event13']}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'events':len(cases),'routes':sum(c['routes'] for c in cases),'samples':sum(c['samples'] for c in cases)}))
if __name__=='__main__':main()
