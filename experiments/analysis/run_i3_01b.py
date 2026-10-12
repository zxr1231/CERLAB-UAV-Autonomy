#!/usr/bin/env python3
"""Execute the one registered six-state two-stage fixture batch; no ROS/no simulation."""
import argparse,json,hashlib,subprocess,math
from pathlib import Path
from i3_route_sampling import sample_route
from exploration_benchmark.sensor_shadow import CameraShadowConfig

def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=args.output;root.mkdir(parents=True,exist_ok=True)
 if (root/'batch_state.json').exists():raise RuntimeError('batch exists; inspect/resume failures explicitly, no silent retry')
 repo=Path(__file__).resolve().parents[2];protofile=repo/'experiments/i3/I3_01B_MINIMAL_PROTOCOL.json';q=json.loads(protofile.read_text());contract=repo/q['contract_file'];assert digest(contract)==q['contract_sha256'];run=Path(q['run_directory']);assert digest(run/'route_controls.jsonl')==q['route_log_sha256'];mapping=repo/'autonomous_flight/cfg/dynamic_exploration/mapping_param.yaml';assert digest(mapping)==q['mapping_yaml_sha256']
 events={int(r['global_sequence']):r['route_controls'] for r in map(json.loads,(run/'route_controls.jsonl').read_text().splitlines())};modes={'camera_reference_only':0,'generic_same_goal':1,'diverse_same_goal':2}
 state={'protocol_sha256':digest(protofile),'status':'RUNNING','cases':[],'new_simulation':False,'source_parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()}
 def save():(root/'batch_state.json').write_text(json.dumps(state,indent=2)+'\n')
 save()
 for case in q['snapshots']:
  seq=case['sequence'];folder=Path(case['directory']);assert case['sha256']=={f.name:digest(f) for f in folder.iterdir() if f.is_file()};planner=json.loads((folder/'planner.json').read_text());e=events[seq]
  candidate=next(c for c in planner['candidate_paths'] if c['id']==case['proposal_candidate']);choice=e['selected_routes'][case['proposal_candidate']];pool=next(x for x in e['pools'] if x['goal_id']==choice['goal_id']);r=next(x for x in pool['candidates'] if x['pool_index']==choice['pool_index'])
  for key,waypoints in [('raw',candidate['raw_waypoints']),('shortcut',candidate['waypoints'])]:
   assert len(r[key])==len(waypoints)
   assert all(max(abs(a-b) for a,b in zip(e['graph_nodes'][node],pose['position']))<=1e-12 for node,pose in zip(r[key],waypoints))
  camera=CameraShadowConfig.from_yaml(mapping,planner['planning_region']['min'],planner['planning_region']['max'])
  request={'sequence':seq,'map_version':planner['map_version'],'accepted':case['safety_accepted_at_recording'],'goal':choice['goal_id'],'start_yaw':case['fixed_start_yaw'],'terminal_yaw':candidate['waypoints'][-1]['yaw'],'nodes':e['graph_nodes'],'edges':e['graph_edges'],'raw':r['raw'],'reference':r['shortcut'],'camera':camera.provenance(),'mode_order':[modes[m] for m in q['mode_order_odd' if seq%2 else 'mode_order_even']]}
  requestfile=root/('request_%06d.json'%seq);requestfile.write_text(json.dumps(request)+'\n');record={'sequence':seq,'stage':case['stage'],'status':'RUNNING'};state['cases'].append(record);save();print('starting',seq,flush=True)
  proc=subprocess.run(['/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/two_stage_fixture_runner',str(folder),str(requestfile)],text=True,capture_output=True,timeout=180)
  (root/('result_%06d.stderr'%seq)).write_text(proc.stderr)
  if proc.returncode:record.update(status='TOOL_ERROR',exit_code=proc.returncode);save();raise RuntimeError('fixture failed state%d'%seq)
  data=json.loads(proc.stdout);out=root/('result_%06d.json'%seq);out.write_text(json.dumps(data,indent=2)+'\n');record.update(status=data['status'],result_sha256=digest(out),result_file=out.name)
  if seq==13:assert data['status']=='SKIP_B_NEGATIVE_CONTROL' and data['camera_calls']==0 and not data['selected'] and not data['trials']
  elif data['status']=='CONTEXT_VALID':
   expected=sample_route(candidate['waypoints'],case['fixed_start_yaw'])['samples'];actual=data['reference_samples'];assert len(expected)==len(actual)
   assert all(max(abs(a-b) for a,b in zip(v['position']+[v['yaw']],w))<=1e-12 for v,w in zip(expected,actual)), 'C++ sampler differs'
   assert len(data['trials'])==9
   for trial in data['trials']:
    assert trial['oracle_match'] and trial['motion_valid']
    if trial['complete']:assert trial['camera_calls']==(1 if trial['mode']==0 else 2) and trial['final_safe'] and trial['total_ms']<=500
    if not trial['alternative']['valid']:assert trial['alternative']['raw']==trial['alternative']['unique']==0 and not trial['alternative']['marginals']
    if trial['fallback'] and trial['selected']:assert trial['selected']==request['reference'] and trial['final_safe']
  assert case['sha256']=={f.name:digest(f) for f in folder.iterdir() if f.is_file()};save();print('done',seq,data['status'],[(t['mode'],t['status'],round(t['total_ms'],2)) for t in data['trials']],flush=True)
 state['status']='COMPLETE';save()
if __name__=='__main__':main()
