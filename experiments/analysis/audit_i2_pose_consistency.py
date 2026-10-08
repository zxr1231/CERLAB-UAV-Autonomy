#!/usr/bin/env python3
"""Read-only audit of reported start-yaw versus candidate motion cost, not I1 evidence."""
import argparse,json,math
from pathlib import Path

def audit(batch_path):
 batch=json.loads(batch_path.read_text());rows=[]
 for run in batch['runs']:
  if run['mode']=='historical_legacy':continue
  for line in (Path(run['result_dir'])/'route_controls.jsonl').read_text().splitlines():
   event=json.loads(line);r=event['route_controls']
   if r['status']!='ready':continue
   pools={p['goal_id']:p for p in r['pools']};goals={p['goal_id']:p for p in r['goal_set'] if p.get('status')=='reachable'}
   for index,(choice,score) in enumerate(zip(r['selected_routes'],r['scores'])):
    ids=pools[choice['goal_id']]['candidates'][choice['pool_index']]['shortcut'];points=[r['graph_nodes'][i] for i in ids]
    previous=r['start_yaw'];yaw=0
    for a,b in zip(points,points[1:]):
     heading=math.atan2(b[1]-a[1],b[0]-a[0]);yaw+=abs(math.remainder(heading-previous,2*math.pi));previous=heading
    yaw+=abs(math.remainder(goals[choice['goal_id']]['terminal_yaw']-previous,2*math.pi))
    rows.append({'mode':run['mode'],'global_sequence':event['global_sequence'],'candidate_index':index,
      'reported_start_yaw':r['start_yaw'],'fixed_start_yaw_cost':yaw,'scored_yaw_cost':score['yaw'],
      'difference_rad':abs(yaw-score['yaw'])})
 return {'schema':'cerlab-i2-pose-consistency-v1','batch':str(batch_path),'candidate_count':len(rows),
  'above_1e_3_rad':sum(r['difference_rad']>1e-3 for r in rows),
  'max_difference_rad':max(r['difference_rad'] for r in rows),
  'interpretation':'new I2 integration preflight defect; frozen offline supply and I1 data/conclusion unaffected',
  'required_followup':'freeze per-plan start position/yaw for new route generation, constraints and scoring; validate callback concurrency before full pilot',
  'rows':rows}

def main():
 p=argparse.ArgumentParser();p.add_argument('batch',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=audit(a.batch);a.output.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='rows'})
if __name__=='__main__':main()
