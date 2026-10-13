#!/usr/bin/env python3
"""One registered fixed-pool observation-loss batch; never modify prior artifacts."""
import argparse,json,hashlib,subprocess
from pathlib import Path
from i3_route_sampling import sample_route
from i3_observation_loss import classify

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
 repo=Path(__file__).resolve().parents[2];protocolfile=repo/'experiments/i3/I3_01C_PROTOCOL.json';q=json.loads(protocolfile.read_text());source=Path(q['source_root']);runner='/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/camera_gain_fixture_runner'
 batch={'status':'RUNNING','protocol_sha256':sha(protocolfile),'source_parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'cases':[]}
 def save():(out/'batch_state.json').write_text(json.dumps(batch,indent=2)+'\n')
 save();all_rows=[]
 for case in q['cases']:
  seq=case['sequence'];folder=Path(case['directory']);assert case['snapshot_sha256']=={f.name:sha(f) for f in folder.iterdir() if f.is_file()}
  assert case['source_files']=={name:sha(source/name) for name in case['source_files']}
  entry={'sequence':seq,'status':'RUNNING'};batch['cases'].append(entry);save()
  if case['status']=='SKIP_B_NEGATIVE_CONTROL':entry['status']='SKIPPED_NEGATIVE_CONTROL';save();continue
  original=json.loads((source/('request_%06d.json'%seq)).read_text());supply=json.loads((source/('result_%06d.json'%seq)).read_text())['operation_supply']['records'];planner=json.loads((folder/'planner.json').read_text());motion=planner['motion_model']
  records=[r for r in supply if r['pool_index'] in case['eligible_pool_indices']];assert len(records)==len(case['eligible_pool_indices'])
  evaluated={}
  for record in records:
   idx=record['pool_index'];evaluated[idx]={}
   for rotational,label in [(True,'full'),(False,'no_rotation_interiors')]:
    evaluated[idx][label]={}
    for layer in ['raw','final']:
     ids=record[layer];points=[{'position':original['nodes'][i],'yaw':original['terminal_yaw']} for i in ids]
     sampled=sample_route(points,original['start_yaw'],q['spacing_m'],q['yaw_spacing_rad'],rotational)
     cost={'length':sampled['length'],'yaw_distance':sampled['yaw_distance'],'time':sampled['length']/motion['velocity']+motion['yaw_penalty_weight']*sampled['yaw_distance']/motion['angular_velocity']}
     prefix='s%03d_p%02d_%s_%s'%(seq,idx,label,layer);request={'config':original['camera'],'samples':sampled['samples'],'estimated_time':cost['time']};req=out/(prefix+'.input.json');req.write_text(json.dumps(request)+'\n')
     print('evaluate',prefix,'poses',len(sampled['samples']),flush=True)
     r=subprocess.run([runner,str(folder),str(req),'--summary-only'],text=True,capture_output=True,timeout=180);(out/(prefix+'.stderr')).write_text(r.stderr);r.check_returncode();d=json.loads(r.stdout);(out/(prefix+'.json')).write_text(json.dumps(d)+'\n')
     assert d['valid'] and d['pose_addresses_omitted'] and not d['pose_addresses'];assert d['map_version']==planner['map_version'];assert sum(d['marginal_gains'])==d['unique_gain']<=d['raw_gain'];assert len(d['unique_addresses'])==len(set(d['unique_addresses']))==d['unique_gain']
     evaluated[idx][label][layer]={'cost':cost,'gain':d,'artifact':prefix+'.json'}
  rows=[]
  for record in records:
   idx=record['pool_index'];row={'sequence':seq,'pool_index':idx,'is_extra':idx!=0,'collapsed_by_shortcut':'shortcut_duplicate' in record['reasons'],'source_reasons':record['reasons']}
   for label in ['full','no_rotation_interiors']:
    x=evaluated[idx][label];baseline=evaluated[0][label]['final'];raw=x['raw'];final=x['final'];r=classify(raw['gain']['unique_addresses'],final['gain']['unique_addresses'],baseline['gain']['unique_addresses'],raw['cost'],baseline['cost'],q,idx!=0)
    r.update({'raw_motion':raw['cost'],'final_motion':final['cost'],'reference_final_motion':baseline['cost'],'raw_raw_gain':raw['gain']['raw_gain'],'final_raw_gain':final['gain']['raw_gain'],'raw_timing_ms':raw['gain']['timing_ms'],'final_timing_ms':final['gain']['timing_ms'],'raw_construction_ms':raw['gain']['construction_ms'],'final_construction_ms':final['gain']['construction_ms'],'raw_artifact':raw['artifact'],'final_artifact':final['artifact']});row[label]=r
   row['yaw_model_sensitive']=any(row['full'][k]!=row['no_rotation_interiors'][k] for k in ['material_predicted_loss','direct_raw_retention_lead','raw_utility_improves']);rows.append(row)
  (out/('state_%06d.json'%seq)).write_text(json.dumps(rows,indent=2)+'\n');all_rows.extend(rows);entry['status']='COMPLETE';entry['rows']=len(rows);save()
  assert case['snapshot_sha256']=={f.name:sha(f) for f in folder.iterdir() if f.is_file()};assert case['source_files']=={name:sha(source/name) for name in case['source_files']}
  print('state complete',seq,flush=True)
 extras=[r for r in all_rows if r['is_extra']];supported=sorted({r['sequence'] for r in extras if r['full']['direct_raw_retention_lead']});lost=[r for r in extras if r['full']['material_predicted_loss']]
 summary={'schema':'i3-01c-observation-loss-v1','protocol_sha256':sha(protocolfile),'rows':all_rows,'candidate_count':len(all_rows),'extra_count':len(extras),'collapsed_extra_count':sum(r['collapsed_by_shortcut'] for r in extras),'material_loss_extra_count':len(lost),'material_loss_states':sorted({r['sequence'] for r in lost}),'raw_as_final_motion_pass_extra_count':sum(r['full']['raw_as_final_motion_pass'] for r in extras),'direct_raw_retention_extra_count':sum(r['full']['direct_raw_retention_lead'] for r in extras),'direct_raw_retention_states':supported,'suggest_further_preservation_design':len(supported)>=q['minimum_supported_states'],'yaw_sensitive_extra_count':sum(r['yaw_model_sensitive'] for r in extras),'no_new_simulation':True,'old_budget_gates_superseded':False,'limitations':['predicted sets under prospective stationary-yaw route sampling, not actual flight observation','raw-vs-raw feasibility does not imply raw-as-final execution feasibility','no partial-preservation search and no online budget admission','one previously used static-scene development corpus; candidates are correlated']}
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');batch['status']='COMPLETE';save();print(json.dumps({k:v for k,v in summary.items() if k not in ['rows']},indent=2),flush=True)
if __name__=='__main__':main()
