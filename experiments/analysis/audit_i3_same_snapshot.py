#!/usr/bin/env python3
"""Registered actual-route audit. Source untouched; all references retained."""
import argparse,json,hashlib,subprocess,time,statistics
from pathlib import Path
from i3_route_sampling import sample_route
from exploration_benchmark.sensor_shadow import CameraShadowConfig
from exploration_benchmark.r1_snapshot import load_snapshot

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 protocol=json.loads(a.protocol.read_text());repo=Path(__file__).resolve().parents[2];run=Path(protocol['run_directory']);mapping=repo/'autonomous_flight/cfg/dynamic_exploration/mapping_param.yaml'
 assert sha(mapping)==protocol['mapping_yaml_sha256'];assert sha(run/'route_controls.jsonl')==protocol['route_log_sha256']
 events={int(e['global_sequence']):e['route_controls'] for e in map(json.loads,(run/'route_controls.jsonl').read_text().splitlines())}
 runner='/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/camera_gain_workload_runner';rows=[]
 for item in protocol['snapshots']:
  folder=Path(item['directory']);assert item['sha256']=={f.name:sha(f) for f in folder.iterdir() if f.is_file()}
  snapshot=load_snapshot(folder);planner=snapshot['planner'];region=planner['planning_region'];seq=item['sequence'];event=events[seq]
  assert event['status']=='ready' and not event['fallback']
  initial_yaw=float(event['start_yaw']);start=event['graph_nodes'][0]
  config=CameraShadowConfig.from_yaml(mapping,region['min'],region['max']);routes=[];descriptions=[];motion=planner['motion_model']
  for candidate in sorted(planner['candidate_paths'],key=lambda x:x['id']):
   assert all(abs(x-y)<=1e-12 for x,y in zip(candidate['waypoints'][0]['position'],start))
   before=time.monotonic();full=sample_route(candidate['waypoints'],initial_yaw,protocol['spacing'],protocol['yaw_spacing']);light=sample_route(candidate['waypoints'],initial_yaw,protocol['spacing'],protocol['yaw_spacing'],False);raw=sample_route(candidate['raw_waypoints'],initial_yaw,protocol['spacing'],protocol['yaw_spacing'])
   estimate=full['length']/motion['velocity']+motion['yaw_penalty_weight']*full['yaw_distance']/motion['angular_velocity'];m=candidate['legacy_metrics']
   assert abs(full['length']-m['path_length'])<=1e-9 and abs(full['yaw_distance']-m['yaw_distance'])<=1e-9 and abs(estimate-m['estimated_time'])<=1e-9,(seq,candidate['id'],'motion mismatch')
   routes.append({'id':candidate['id'],'estimated_time':estimate,'samples':full['samples'],'translation_only_samples':light['samples']})
   descriptions.append({'id':candidate['id'],'length_m':full['length'],'yaw_rad':full['yaw_distance'],'estimated_time':estimate,'full_samples':len(full['samples']),'translation_only_samples':len(light['samples']),'raw_samples':len(raw['samples']),'raw_length_m':raw['length'],'sampling_python_ms':1000*(time.monotonic()-before)})
  request={'config':config.provenance(),'routes':routes,'repeats':protocol['repeats'],'count_diagnostics':protocol['candidate_count_diagnostics'],'budget_ms':protocol['budget_ms'],'sampler':protocol['sampler']}
  f=a.output/('request_%06d.json'%seq);f.write_text(json.dumps(request)+'\n');print('state',seq,'references',len(routes),'full poses',sum(x['full_samples'] for x in descriptions),flush=True)
  result=subprocess.run([runner,str(folder),str(f)],text=True,capture_output=True,timeout=180)
  (a.output/('result_%06d.stderr'%seq)).write_text(result.stderr);result.check_returncode();data=json.loads(result.stdout);(a.output/('result_%06d.json'%seq)).write_text(json.dumps(data,indent=2)+'\n')
  assert len(data['repeats'])==3 and data['actual_candidates']==len(routes)
  signature=lambda r:[(x['id'],x['raw_gain'],x['unique_gain'],x['marginals'],x['sample_count']) for x in r['routes']]
  assert all(signature(r)==signature(data['repeats'][0]) for r in data['repeats']), 'compute-repeat gain mismatch'
  expected={x['id']:x for x in data['repeats'][0]['routes']}
  for x in data['budget_guard']['routes']:
   if x['valid']:
    y=expected[x['id']];assert x['raw_gain']==y['raw_gain'] and x['unique_gain']==y['unique_gain'] and x['marginals']==y['marginals']
   else:assert x['raw_gain']==x['unique_gain']==0 and not x['marginals']
  assert data['budget_guard']['fallback']==(data['budget_guard']['completed_references']!=len(routes))
  costs=[x['preparation_scoring_ms'] for x in data['repeats']];guard=data['budget_guard']
  row={'sequence':seq,'snapshot_map_version':data['map_version'],'original_planning_map_version':event['map_version'],'map_epochs_differ':data['map_version']!=event['map_version'],'fixed_start_yaw':initial_yaw,'export_live_yaw':planner['vehicle']['yaw'],'reference_count':len(routes),'route_descriptions':descriptions,'all_reference_ms':costs,'maximum_all_reference_ms':max(costs),'preparation_ms':[x['preparation_ms'] for x in data['repeats']],'scoring_ms':[x['scoring_ms'] for x in data['repeats']],'translation_only_scoring_ms':[x['translation_only_scoring_ms'] for x in data['repeats']],'primary_cost_pass':max(costs)<=protocol['budget_ms'],'guard':guard,'guard_overshoot_pass':guard['overshoot_ms']<=protocol['overshoot_ms_max'],'count_diagnostics':data['repeats'][0]['count_diagnostics'],'peak_rss_mib':data['peak_rss_mib'],'snapshot_sha256':item['sha256']}
  rows.append(row);(a.output/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('done',seq,'whole max ms',max(costs),'guard completed',guard['completed_references'],'/',len(routes),flush=True)
  assert item['sha256']=={f.name:sha(f) for f in folder.iterdir() if f.is_file()},'frozen input changed'
 summary={'schema':'i3-00-same-snapshot-audit-v1','protocol_sha256':sha(a.protocol),'states':rows,'state_count':len(rows),'all_reference_admission':all(r['primary_cost_pass'] for r in rows),'all_guards_overshoot_pass':all(r['guard_overshoot_pass'] for r in rows),'no_incomplete_goal_set_accepted':all(r['guard']['fallback']==(r['guard']['completed_references']<r['reference_count']) for r in rows),'unavailable_counts_explicit':True,'translation_only_not_admission':True,'kernel_commit':protocol['kernel_commit'],'source_unchanged':sha(run/'route_controls.jsonl')==protocol['route_log_sha256'] and sha(mapping)==protocol['mapping_yaml_sha256'],'limitations':['one prior static-scene run, six dependent fixed states, not exploration performance','mandatory distance references only, no invented15/30 distinct routes','stationary shortest corner-yaw poses are prospective, not executed B-spline truth','map copy/model/kernel measured; live capture lock/search/safety/sampling integration not measured','subsets omit Goals and cannot replace full-reference gate']}
 (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('all references admitted',summary['all_reference_admission'],flush=True)
if __name__=='__main__':main()
