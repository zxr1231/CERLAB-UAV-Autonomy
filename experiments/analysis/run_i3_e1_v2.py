#!/usr/bin/env python3
"""One V2 E1 batch with immutable per-state checkpoints and complete artifact identity."""
import argparse,json,hashlib,subprocess,time,traceback
from pathlib import Path
from i3_e1_foundation import choices,decision
from i3_route_sampling import sample_route
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fp(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
 repo=Path(__file__).resolve().parents[2];pf=repo/'experiments/i3/I3_02E_PROTOCOL_V2.json';rf=repo/'experiments/i3/I3_02E_INPUTS_V2.json';q=json.loads(pf.read_text());reg=json.loads(rf.read_text())
 runner=Path('/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/corridor_fixture_runner')
 identity={'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'global_planner_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo/'global_planner',text=True).strip(),'runner_sha256':sha(runner),'protocol_sha256':sha(pf),'registry_sha256':sha(rf)}
 batch={'status':'RUNNING','identity':identity,'states':[]};write(out/'batch_state.json',batch)
 def check(c):
  folder=Path(c['snapshot_directory']);assert c['snapshot_sha256']=={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
  assert all(sha(Path(reg['source_root'])/n)==h for n,h in c['source_sha256'].items())
  assert fp(c['context'])==c['context_fingerprint'] and fp(c['context']['camera'])==c['camera_fingerprint']
  assert sha(runner)==identity['runner_sha256']
 def invoke(mode,c,label,poolfile=None):
  command=[str(runner),mode,c['snapshot_directory'],c['request_file']]+([str(poolfile)] if poolfile else [])
  start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,timeout=180)
  (out/(label+'.stderr')).write_text(r.stderr)
  if r.returncode:
   (out/(label+'.failed_stdout')).write_text(r.stdout);r.check_returncode()
  d=json.loads(r.stdout);d['external_process_wall_ms']=(time.monotonic()-start)*1000;d['context_fingerprint']=c['context_fingerprint'];write(out/(label+'.json'),d);return d
 def verify_metrics(m):
  assert len(m['addresses'])==len(set(m['addresses']))==m['unique'];assert m['addresses']==sorted(m['addresses']);assert sum(m['marginal'])==m['unique']<=m['raw']
 states=[]
 try:
  for c in reg['cases']:
   seq=c['sequence'];entry={'sequence':seq,'status':'RUNNING'};batch['states'].append(entry);write(out/'batch_state.json',batch);check(c)
   prefix='s%03d'%seq;pool=invoke('pool',c,prefix+'_pool')
   if seq==13:
    assert pool['status']=='SKIP_NEGATIVE_CONTROL' and pool['camera_calls']==pool['pairs_enumerated']==0
    entry['status']='SKIPPED_NEGATIVE_CONTROL';write(out/'batch_state.json',batch);continue
   assert pool['status']=='CONTEXT_VALID' and pool['camera_calls']==0 and len(pool['records'])<=12000 and len(pool['pool'])<=5
   request=json.loads(Path(c['request_file']).read_text());rows=pool['records'];assert all(not rows[i]['reasons'] for i in pool['pool'])
   n=len(pool['ordered']);expected=pool['ordered'] if n<=5 else [pool['ordered'][j*(n-1)//4] for j in range(5)];assert expected==pool['pool']
   for id in pool['pool']:
    r=rows[id];motion=r['motion'];ref=pool['reference_motion'];assert motion['length']<=1.25*ref['length'] and motion['time']<=1.25*ref['time'] and motion['yaw']<=ref['yaw']+q['motion']['extra_yaw_max']
    points=[{'position':request['nodes'][i],'yaw':request['terminal_yaw']} for i in r['path']];poses=sample_route(points,request['start_yaw'])['samples'];assert len(poses)==len(r['samples'])
    assert all(max(abs(a-b) for a,b in zip(x['position']+[x['yaw']],y['position']+[y['yaw']]))<=1e-12 for x,y in zip(poses,r['samples']))
   poolfile=out/(prefix+'_pool.json');composed=invoke('compose',c,prefix+'_compose',poolfile);assert composed['valid'] and composed['status']=='COMPLETE' and not composed['allocation_limit_rejected']
   assert composed['visibility_requested_peak_bytes']<=q['api_budget']['visibility_scratch_bytes'];verify_metrics(composed['reference'])
   old=json.loads(Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-01C-OBSERVATION-LOSS-V1',prefix+'_p00_full_final.json').read_text())
   mapping={'raw':'raw_gain','unique':'unique_gain','addresses':'unique_addresses','marginal':'marginal_gains'}
   assert all(composed['reference'][k]==old[v] for k,v in mapping.items())
   assert len(composed['rows'])==len(pool['pool'])
   for r in composed['rows']:
    verify_metrics(r['metrics']);R=set(composed['reference']['addresses']);V=set(r['metrics']['addresses']);assert r['new']==len(V-R) and r['lost']==len(R-V)
   selected=choices(pool,composed['rows'],composed['reference']['unique'],pool['reference_motion']['time'])
   checkpoint={'sequence':seq,'choices':selected,'compose_sha256':sha(out/(prefix+'_compose.json')),'identity':identity};write(out/(prefix+'_selection.json'),checkpoint);entry['selection_sha256']=sha(out/(prefix+'_selection.json'));entry['status']='SELECTION_FROZEN';write(out/'batch_state.json',batch)
   oracle=invoke('oracle',c,prefix+'_oracle',poolfile);oref=oracle['rows'][0]['metrics'];assert composed['reference']==oref
   orows={r['record_id']:r['metrics'] for r in oracle['rows'][1:]};assert all(r['metrics']==orows[r['record_id']] for r in composed['rows'])
   from_oracle=[dict(r,metrics=orows[r['record_id']],utility=orows[r['record_id']]['unique']/r['time']) for r in composed['rows']]
   assert choices(pool,from_oracle,oref['unique'],pool['reference_motion']['time'])==selected
   # All complete state outcomes, including no useful route, remain in the denominator.
   reference_u=composed['reference']['unique']/pool['reference_motion']['time']
   state={'sequence':seq,'stage':c['stage'],'status':'COMPLETE','pool_size':len(pool['pool']),'qualified':len(pool['ordered']),'possible_pairs':pool['possible_pairs'],'enumerated_pairs':len(rows),'truncated':pool['truncated'],'reference_unique':composed['reference']['unique'],'reference_time':pool['reference_motion']['time'],'reference_utility':reference_u,'choices':selected,'engineering_parity':True,'rows':[dict(r,metrics_file=prefix+'_compose.json') for r in composed['rows']], 'generation_component_ms':pool['generation_component_ms'],'compose_process_ms':composed['external_process_wall_ms'],'oracle_process_ms':oracle['external_process_wall_ms'],'scratch_peak_bytes':composed['visibility_requested_peak_bytes'],'pose_queries':composed['shared_camera_pose_queries'],'voxel_visits':composed['shared_voxel_visits']}
   write(out/('state_%06d.json'%seq),state);states.append(state);check(c);entry['status']='COMPLETE';entry['state_sha256']=sha(out/('state_%06d.json'%seq));write(out/'batch_state.json',batch);print('state complete',seq,'pool',len(pool['pool']),flush=True)
  summary={'schema':'i3-e1-foundation-v2','identity':identity,'states':states,**decision(states),'states_denominator':5,'negative_control':13,'new_simulation':False,'optical_model_changed':False,'stage_b_budget_tested':False,'no_guided_generation_claim':True}
  write(out/'summary.json',summary);batch['status']='COMPLETE';batch['decision']=summary['decision'];write(out/'batch_state.json',batch);print(json.dumps({k:v for k,v in summary.items() if k!='states'},indent=2),flush=True)
 except Exception as e:
  batch['status']='ENGINEERING_OR_RESOURCE_FAIL';batch['error']=str(e);write(out/'batch_state.json',batch);(out/'failure_traceback.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
