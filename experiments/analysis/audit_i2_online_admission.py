#!/usr/bin/env python3
"""Audit preregistered I2 fixed-pose online admission without relabeling raw runs."""
import argparse, json, math
from pathlib import Path
from summarize_i2_smoke import audit as audit_smoke
from audit_i2_pose_consistency import audit as audit_pose

def percentile(values,p):
 values=sorted(values)
 if not values:return None
 at=(len(values)-1)*p;lo=int(at);hi=min(lo+1,len(values)-1)
 return values[lo]+(values[hi]-values[lo])*(at-lo)

def audit(batch_path,protocol_path):
 protocol=json.loads(protocol_path.read_text());batch=json.loads(batch_path.read_text())
 smoke=audit_smoke(batch_path);pose=audit_pose(batch_path)
 limits=protocol['checks'];output={'protocol_id':protocol['protocol_id'],'runs':[],'pose_audit':pose,'scope':'online admission only; full paired pilot not run'}
 for basic,registered in zip(smoke['runs'],batch['runs']):
  folder=Path(registered['result_dir']);start=json.loads((folder/'planning_start.json').read_text())['sim_time']
  raw=[json.loads(line) for line in (folder/'route_controls.jsonl').read_text().splitlines()]
  ready=[r for r in raw if r['route_controls']['status']=='ready' and not r['route_controls']['fallback']]
  late_extra=[];durations=[];context_ok=True;max_length_error=0;max_constraint_yaw_error=0
  for event in ready:
   row=event['route_controls'];durations.append(row['alternative_elapsed_ms'])
   reference_count=sum(g.get('status')=='reachable' for g in row['goal_set'])
   extra=row['selected_count']-reference_count
   if extra>0 and event['sim_time']-start>35:late_extra.append({'global_sequence':event['global_sequence'],'elapsed_sim':event['sim_time']-start,'extra':extra})
   context_ok=context_ok and row.get('pose_context_schema')==1 and row.get('pose_sequence',0)>0 and math.isfinite(row.get('pose_stamp',float('nan')))
   goals={g['goal_id']:g for g in row['goal_set'] if g.get('status')=='reachable'}
   for pool in row['pools']:
    for c in pool['candidates']:
     if not c['shortcut'] or c['rejections']:continue
     points=[row['graph_nodes'][i] for i in c['shortcut']]
     length=sum(math.sqrt(sum((b[i]-a[i])**2 for i in range(3))) for a,b in zip(points,points[1:]))
     yaw=0;previous=row['start_yaw']
     for a,b in zip(points,points[1:]):
      heading=math.atan2(b[1]-a[1],b[0]-a[0]);yaw+=abs(math.remainder(heading-previous,2*math.pi));previous=heading
     yaw+=abs(math.remainder(goals[pool['goal_id']]['terminal_yaw']-previous,2*math.pi))
     max_length_error=max(max_length_error,abs(length-c['shortcut_length']))
     max_constraint_yaw_error=max(max_constraint_yaw_error,abs(yaw-c['shortcut_yaw']))
  pose_rows=[r for r in pose['rows'] if r['mode']==registered['mode']]
  yaw_error=max((r['difference_rad'] for r in pose_rows),default=None)
  elapsed95=percentile(durations,.95);maximum=max(durations,default=None)
  checks=dict(basic['checks'])
  checks.update({'frozen_pose_metadata':context_ok and bool(ready),
   'fixed_yaw_scoring':yaw_error is not None and yaw_error<=limits['fixed_start_yaw_max_error_rad'],
   'fixed_pose_constraints':max_length_error<=1e-9 and max_constraint_yaw_error<=1e-9,
   'ready_plan_min':len(ready)>=limits['ready_plan_count_min'],
   'post35_supply':len(late_extra)>=3,
   'alternative_p95':elapsed95 is not None and elapsed95<=limits['alternative_elapsed_p95_ms_max'],
   'alternative_max':maximum is not None and maximum<=limits['alternative_elapsed_max_ms_max'],
   'rtf':basic['rtf']['mean']>=limits['rtf_mean_min'],
   'no_adapter_error':all(r['route_controls']['status']!='adapter_error' for r in raw)})
  output['runs'].append({'mode':registered['mode'],'result_dir':str(folder),'checks':checks,'passed':all(checks.values()),
   'ready_plans':len(ready),'post35_extra_plans':late_extra,'max_scored_yaw_error_rad':yaw_error,
   'max_constraint_yaw_error_rad':max_constraint_yaw_error,'max_geometry_length_error_m':max_length_error,
   'alternative_p95_ms':elapsed95,'alternative_max_ms':maximum,'rtf_mean':basic['rtf']['mean'],
   'fallback_count':sum(r['route_controls']['fallback'] for r in raw),'original_outcome':registered['outcome'],
   'global_planning':basic['global_planning'],'mission_distance':basic['mission_distance']})
 output['passed']=all(r['passed'] for r in output['runs'])
 return output

def main():
 p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=audit(a.batch,a.protocol);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 for r in result['runs']:print(r['mode'],'passed',r['passed'],'ready',r['ready_plans'],'post35',len(r['post35_extra_plans']),'yaw_error',r['max_scored_yaw_error_rad'],'p95',r['alternative_p95_ms'],'max',r['alternative_max_ms'])
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
