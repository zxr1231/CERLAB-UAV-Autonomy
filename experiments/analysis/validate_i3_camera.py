#!/usr/bin/env python3
"""Frozen I2 held-out per-pose C++/Python parity and fixed evaluator cost check."""
import argparse,csv,json,subprocess,statistics,hashlib,time
from pathlib import Path
from exploration_benchmark.r1_snapshot import load_snapshot,load_frozen_map
from exploration_benchmark.predicted_observation import sample_odom_prefix
from exploration_benchmark.sensor_shadow import CameraShadowConfig,visible_unknown_shadow,camera_unit_rays

def percentile(values,p):
 s=sorted(values);at=(len(s)-1)*p;lo=int(at);hi=min(lo+1,len(s)-1);return s[lo]+(s[hi]-s[lo])*(at-lo)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 project=Path(__file__).resolve().parents[2];source=Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I2-06-HELD-OUT-SEED4-V1');raw=source/'environment_seed_004/planner_seed_004/20261012T140548';selected=json.loads((source/'analysis/selected_intervals.json').read_text())['selected_ids_and_stage']
 previous={r['interval_id']:r for r in map(json.loads,(source/'analysis/sensor_shadow_sets.jsonl').read_text().splitlines())}
 with (raw/'trajectory.csv').open() as f:trajectory=list(csv.DictReader(f))
 intervals={}
 for r in trajectory:intervals.setdefault(int(r['execution_interval_id']),[]).append(r)
 with (raw/'execution_intervals.csv').open() as f:meta={int(r['interval_id']):r for r in csv.DictReader(f)}
 frozen_hash={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [raw/'trajectory.csv',raw/'execution_intervals.csv',source/'analysis/sensor_shadow_sets.jsonl',source/'analysis/selected_intervals.json']}
 rows=[];requests=[]
 runner='/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/camera_gain_fixture_runner'
 for key,stage in selected.items():
  identifier=int(key);folder=raw/'snapshots'/('execution_%06d'%identifier);snapshot=load_snapshot(folder);grid=load_frozen_map(folder,snapshot);region=snapshot['planner']['planning_region'];config=CameraShadowConfig.from_yaml(project/'autonomous_flight/cfg/dynamic_exploration/mapping_param.yaml',region['min'],region['max']);samples=sample_odom_prefix(intervals[identifier],.25,.1)
  request={'config':config.provenance(),'samples':samples,'estimated_time':float(meta[identifier]['duration_sim'])};inputpath=a.output/('input_%06d.json'%identifier);inputpath.write_text(json.dumps(request)+'\n');requests.append({'snapshot':str(folder),'input':str(inputpath)})
  print('parity interval',identifier,'poses',len(samples),flush=True)
  began=time.monotonic();p=subprocess.run([runner,str(folder),str(inputpath)],text=True,capture_output=True,timeout=180);(a.output/('cpp_%06d.stderr'%identifier)).write_text(p.stderr);p.check_returncode();cpp=json.loads(p.stdout);(a.output/('cpp_%06d.json'%identifier)).write_text(json.dumps(cpp)+'\n')
  union=set();raw_count=0;marginal=[];pose_mismatches=[];rays=camera_unit_rays(config)
  for i,pose in enumerate(samples):
   visible=set(visible_unknown_shadow(grid,pose['position'],pose['yaw'],config,rays));got=set(cpp['pose_addresses'][i]);raw_count+=len(visible);marginal.append(len(visible-union));union.update(visible)
   if got!=visible:pose_mismatches.append({'sample':i,'cpp_only':sorted(got-visible),'python_only':sorted(visible-got)})
  parity=not pose_mismatches and cpp['raw_gain']==raw_count and cpp['marginal_gains']==marginal and set(cpp['unique_addresses'])==union and set(previous[identifier]['addresses'])==union and cpp['map_version']==grid.version
  row={'interval_id':identifier,'stage':stage,'sample_count':len(samples),'parity':parity,'pose_mismatches':pose_mismatches,'python_raw_gain':raw_count,'python_unique_gain':len(union),'cpp_raw_gain':cpp['raw_gain'],'cpp_unique_gain':cpp['unique_gain'],'timing_ms':cpp['timing_ms'],'ray_count':cpp['ray_count'],'construction_ms':cpp['construction_ms'],'voxel_visits':cpp['voxel_visits'],'total_comparison_wall_seconds':time.monotonic()-began,'snapshot_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}}
  rows.append(row);(a.output/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('done',identifier,'parity',parity,'times',cpp['timing_ms'],flush=True)
 (a.output/'batch_request.json').write_text(json.dumps(requests)+'\n')
 timings=[t for r in rows for t in r['timing_ms']]
 assert frozen_hash=={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in frozen_hash}
 result={'schema':'i3-00-camera-parity-v1','rows':rows,'all_exact':all(r['parity'] for r in rows),'prefix_p95_ms':percentile(timings,.95),'prefix_max_ms':max(timings),'prefix_cost_gate':percentile(timings,.95)<=250 and max(timings)<=500,'batch_gate':'PENDING_ACTUAL_BATCH_PROBE','frozen_input_sha256':frozen_hash}
 (a.output/'parity_summary.json').write_text(json.dumps(result,indent=2)+'\n');print('parity complete',result['all_exact'],result['prefix_p95_ms'],flush=True)
if __name__=='__main__':main()
