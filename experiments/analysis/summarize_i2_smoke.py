#!/usr/bin/env python3
"""Audit bounded I2 integration smoke; never change raw outcomes or pilot evidence."""
import argparse,csv,json,hashlib
from collections import Counter
from pathlib import Path

def load(path):return json.loads(path.read_text())
def audit(statefile):
 state=load(statefile)
 if state['status']!='collected':raise RuntimeError('batch not fully collected')
 result={'schema':'cerlab-i2-04-smoke-audit-v1','batch':str(statefile),'interpretation':'bounded safety/integration only; no T95 or method superiority claim','runs':[]}
 for registered in state['runs']:
  path=Path(registered['result_dir']);manifest=load(path/'run.json');summary=load(path/'summary.json')
  checks={
   'expected_bounded_outcome':manifest['outcome'] in ('TIMEOUT','HOME_REACHED') and not manifest.get('error'),
   'same_mode_registered':manifest['route_control_mode']==registered['mode'],
   'collision_valid_and_zero':summary['collision']['status']=='VALID' and summary['collision']['episode_count']==0,
   'resources_valid':manifest.get('resource_metrics_status')=='VALID',
   'trajectory_valid':manifest.get('trajectory_metrics_status')=='VALID',
   'movement':summary.get('mission_distance',0)>1,
   'rosbag_disabled':manifest['record_rosbag'] is False,
   'four_route_layers':False,
  }
  records=[loadline for line in (path/'planned_paths.jsonl').read_text().splitlines() if (loadline:=json.loads(line))]
  checks['four_route_layers']={'prm_raw','prm','input','bspline'}<={p['kind'] for p in records}
  executions=list(csv.DictReader((path/'execution_intervals.csv').open()))
  checks['execution_linkage']=bool(executions) and any(int(r.get('global_sequence') or 0)>0 and float(r.get('executed_distance') or 0)>0 for r in executions)
  log=(path/'exploration.log').read_text(errors='replace')
  checks['no_crash_log']=not any(x in log for x in ['exit code -11','Segmentation fault','Traceback (most recent call last)'])
  rows=[];extras={}
  if registered['mode']=='historical_legacy':checks['default_has_no_new_route_log']=not (path/'route_controls.jsonl').exists()
  else:
   rows=[json.loads(line) for line in (path/'route_controls.jsonl').read_text().splitlines()]
   ready=[r for r in rows if r['route_controls']['status']=='ready' and not r['route_controls']['fallback']]
   checks['ready_candidates']=bool(ready)
   checks['candidate_count_contract']=all(0<r['route_controls']['selected_count']==r['route_controls']['scored_count']<=r['route_controls']['post_shortcut_unique']<=r['route_controls']['motion_feasible']<=r['route_controls']['raw_generated'] for r in ready)
   checks['common_shadow_snapshot']=all(all(s.get('unique_valid') and s.get('unique_map_version')==r['route_controls']['map_version'] for s in r['route_controls']['scores']) for r in ready)
   comparisons=[c for r in ready for c in r['route_controls']['astar_comparisons']]
   checks['frozen_astar_comparisons']=bool(comparisons) and all(c['snapshot_matches_comparison_map'] for c in comparisons)
   checks['snapshot_validation_logged']=all('validation_map_version' in r['route_controls'] and 'validation_route_safe' in r['route_controls'] for r in ready)
   unsafe={r['global_sequence'] for r in ready if not r['route_controls']['validation_route_safe']}
   executed={int(r['global_sequence']) for r in executions if int(r.get('global_sequence') or 0)>0}
   checks['unsafe_selection_not_executed']=not (unsafe&executed)
   extras={'route_events':len(rows),'ready_events':len(ready),'fallback_events':sum(r['route_controls']['fallback'] for r in rows),
    'total_raw':sum(r['route_controls']['raw_generated'] for r in ready),
    'total_post_shortcut_unique':sum(r['route_controls']['post_shortcut_unique'] for r in ready),
    'total_scored':sum(r['route_controls']['scored_count'] for r in ready),
    'astar_comparison_count':len(comparisons),'astar_max_excess_length':max((c.get('excess_length',0) for c in comparisons),default=None),
    'unsafe_rejections':len(unsafe),'snapshot_changed_before_validation':sum(r['route_controls']['planning_snapshot_changed'] for r in ready)}
  if registered['mode']!='historical_legacy':
   reasons=Counter(); goals=surviving=0
   for row in rows:
    for pool in row['route_controls'].get('pools',[]):
     goals+=1;surviving+=max(0,pool['post_shortcut_unique']-1)
     for candidate in pool['candidates']:reasons.update(candidate['rejections'])
   extras['reachable_goal_instances']=goals
   extras['surviving_alternatives']=surviving
   extras['rejection_counts']=dict(reasons)
  result['runs'].append({'mode':registered['mode'],'result_dir':str(path),'source_commit':manifest['main_commit'],
    'original_outcome':manifest['outcome'],'original_run_status':manifest['status'],'checks':checks,
    'passed':all(checks.values()),'mission_distance':summary['mission_distance'],'rtf':summary['rtf'],
    'global_planning':summary['planning'].get('global'),'details':extras,
    'run_json_sha256':hashlib.sha256((path/'run.json').read_bytes()).hexdigest()})
 result['passed']=all(r['passed'] for r in result['runs'])
 result['next_gate']='I2-05 must preregister candidate-supply/coverage-of-planning-phases diagnostics before committing full paired pilot.'
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('batch_state',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 result=audit(args.batch_state);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
