#!/usr/bin/env python3
"""Summarize FIRST attempts, retain failure/censoring and user-directed early stop."""
import csv,json,statistics,hashlib,argparse
from pathlib import Path
from exploration_benchmark.aggregate import summarize_run,first_state_time,load_jsonl,latest_at_or_before
ROOT=Path(__file__).resolve().parent
MODES=['historical_legacy','distance_single','generic_k_shortest','geometric_diverse']
METRICS=['t80_seconds','t90_seconds','t95_seconds','exploration_duration_sim','exploration_distance_m','free_coverage','global_planning_mean_ms','global_planning_p95_ms','exploration_cpu_mean','exploration_rss_mean_mib','mean_rtf','sensor_new_voxels_per_meter_until_stop','sensor_new_voxels_per_second_until_stop']
def read(p):return json.loads(p.read_text())
def distribution(values,total):
 finite=[v for v in values if v is not None]
 return {'observed_count':len(finite),'total_trials':total,'missing_or_censored_count':total-len(finite),'mean_uncensored':statistics.mean(finite) if finite else None,'median_uncensored':statistics.median(finite) if finite else None,'sample_std_uncensored':statistics.stdev(finite) if len(finite)>1 else None,'values_in_seed_order':values}
def main():
 global ROOT
 parser=argparse.ArgumentParser();parser.add_argument('--batch-root',type=Path,default=Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I2-05-PAIRED-PILOT-V1'))
 ROOT=parser.parse_args().batch_root.resolve()
 state=read(ROOT/'batch_state.json');rows=[];errors=[];reference_files=None;reference_submodules=None
 for task in state['tasks']:
  if task['status'] in ('PENDING','RUNNING','INTERRUPTED'):raise RuntimeError('collection not finished')
  if len(task['attempts'])!=1:raise RuntimeError('first-attempt policy needs reconciliation')
  attempt=task['attempts'][0]
  if not attempt.get('result_dir'):
   errors.append(task['task_id']+' missing result');continue
  d=Path(attempt['result_dir']);run=read(d/'run.json');summary=read(d/'summary.json')
  if run['main_commit']!=state['source_commit'] or run['git_status']:errors.append(task['task_id']+' source mismatch')
  if reference_files is None:reference_files=run['files'];reference_submodules=run['submodules']
  elif run['files']!=reference_files or run['submodules']!=reference_submodules:errors.append(task['task_id']+' config mismatch')
  row=summarize_run(d,task['task_id'],1,task['status']);row['route_mode']=task['route_control_mode'];row['matrix_status']=task['status']
  events=load_jsonl(d/'events.jsonl');stop=first_state_time(events,{'RETURNING_HOME','RETURN_BLOCKED'})
  if stop is None:stop=summary['sim_end']
  start=run['planning_start_sim']
  with (d/'coverage.csv').open() as f:coverage=list(csv.DictReader(f))
  counts=[int(c['accessible_observed']) for c in coverage]
  if counts!=sorted(counts):errors.append(task['task_id']+' nonmonotonic observation counter')
  initial=latest_at_or_before(coverage,start);final=latest_at_or_before(coverage,stop)
  with (d/'trajectory.csv').open() as f:trajectory=list(csv.DictReader(f))
  endpose=latest_at_or_before(trajectory,stop)
  duration=stop-start;distance=float(endpose['mission_distance']) if endpose else None
  delta=int(final['accessible_observed'])-int(initial['accessible_observed']) if initial and final else None
  row.update({'observed_until_sim':stop,'stop_is_exploration_completion':row['algorithm_completed'],
    'sensor_new_accessible_voxels_until_stop':delta,'sensor_new_voxels_per_meter_until_stop':delta/distance if delta is not None and distance else None,
    'sensor_new_voxels_per_second_until_stop':delta/duration if delta is not None and duration>0 else None})
  row['threshold_reached_before_exploration_completion']={key:bool(row[key+'_seconds'] is not None and row['completion_sim'] is not None and start+row[key+'_seconds']<=row['completion_sim']) for key in ['t80','t90','t95']}
  routefile=d/'route_controls.jsonl'
  if routefile.exists():
   route=[r for r in load_jsonl(routefile) if r['route_controls']['status']=='ready' and not r['route_controls']['fallback']]
   row['ready_route_plans']=len(route);row['plans_with_extra_selected_routes']=sum(r['route_controls']['selected_count']>sum(g.get('status')=='reachable' for g in r['route_controls']['goal_set']) for r in route)
  row['run_json_sha256']=hashlib.sha256((d/'run.json').read_bytes()).hexdigest();rows.append(row)
 groups={}
 for mode in MODES:
  selected=sorted([r for r in rows if r['route_mode']==mode],key=lambda r:r['environment_seed'])
  groups[mode]={'n':len(selected),'success':sum(r['return_success'] for r in selected),'algorithm_completed':sum(r['algorithm_completed'] for r in selected),'collision_episodes':sum(r['collision_episodes'] or 0 for r in selected),'statuses':[r['matrix_status'] for r in selected],
   'metrics':{m:distribution([r[m] if not (m.startswith('t') and m.endswith('_seconds') and r.get(m.replace('_seconds','_censored'))) else None for r in selected],len(selected)) for m in METRICS}}
 contrasts={}
 for candidate,baseline in [('generic_k_shortest','distance_single'),('geometric_diverse','distance_single'),('geometric_diverse','generic_k_shortest'),('distance_single','historical_legacy')]:
  key=candidate+' minus '+baseline;contrasts[key]={}
  for metric in METRICS:
   values=[]
   for seed in [1,2,3]:
    a=next(r for r in rows if r['route_mode']==candidate and r['environment_seed']==seed);b=next(r for r in rows if r['route_mode']==baseline and r['environment_seed']==seed)
    x,y=a[metric],b[metric]
    if metric.startswith('t') and metric.endswith('_seconds') and (a.get(metric.replace('_seconds','_censored')) or b.get(metric.replace('_seconds','_censored'))):x=None
    values.append(x-y if x is not None and y is not None else None)
   contrasts[key][metric]=distribution(values,3)
 report={'schema':'cerlab-i2-05-paired-summary-v1','source_commit':state['source_commit'],'errors':errors,'trial_count':len(rows),'groups':groups,'contrasts':contrasts,'runs':rows,
  'limitations':['N3 exploratory paired pilot; no significance or generality claim','Retain user-aborted seed1 distance trial; first attempt, not replaced','Missing/censored thresholds are explicit; uncensored-only means are not unconditional method rankings','Raw T thresholds retain frozen whole-run convention; pre-return reach flags are supplemental','Sensor observation rates until stop include stalled time for failures; cannot rank methods by per-metre rate alone','No executed counterfactual observation for unselected routes']}
 (ROOT/'paired_summary.json').write_text(json.dumps(report,indent=2)+'\n');print('summarized',len(rows),'errors',errors)
if __name__=='__main__':main()
