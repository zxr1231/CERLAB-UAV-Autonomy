#!/usr/bin/env python3
"""Read-only aggregate of preregistered I2-05 frozen candidate-supply diagnostics."""
import argparse, hashlib, json
from pathlib import Path
from collections import Counter

def summarize(protocol_path,root):
 protocol=json.loads(protocol_path.read_text());state=json.loads((root/'batch_state.json').read_text())
 assert state['status']=='complete' and state['repeat_exact_non_timing']
 assert state['protocol_sha256']==hashlib.sha256(protocol_path.read_bytes()).hexdigest()
 registered={r['name']:r for r in protocol['snapshots']}
 assert len(state['snapshots'])==len(registered)==24
 assert {r['name'] for r in state['snapshots']}==set(registered)
 cases={};snapshot_rows=[];missing=unreachable=reachable=0
 for entry in state['snapshots']:
  assert entry['status']=='complete' and entry['phase']==registered[entry['name']]['phase']
  path=root/(entry['name']+'.json');assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
  row=json.loads(path.read_text());assert row['map_version']==registered[entry['name']]['map_version']
  assert [t['k'] for t in row['trials']]==protocol['diagnostic_pool_sizes']
  status=Counter(g['status'] for g in row['goals']);missing+=status['missing_goal'];unreachable+=status['unreachable'];reachable+=status['reachable']
  snap={'name':entry['name'],'phase':entry['phase'],'reachable_goals':row['reachable_goals'],'trials':[]}
  for trial in row['trials']:
   assert trial['alternative_pops']<=protocol['primary']['heap_pops_global']
   assert all(g['pops']<=protocol['primary']['heap_pops_per_goal'] for g in trial['goals'])
   short={'k':trial['k']}
   for variant in ['strict','post_only','no_motion']:
    key=(trial['k'],variant)
    if key not in cases:cases[key]={'k':key[0],'constraints':key[1],'positive_snapshots':0,'positive_by_phase':Counter(),'selected_extra_routes':0,'selection_list_changed_snapshots':0,'raw_generated':0,'motion_feasible':0,'post_shortcut_unique':0,'heap_cutoff_goal_instances':0,'rejection_counts':Counter()}
    case=cases[key];extras=trial[variant]['selected_extra_count'];short[variant+'_extra']=extras
    assert extras==trial[variant]['generic_selected_count']-row['reachable_goals'] and extras>=0
    case['positive_snapshots']+=extras>0;case['positive_by_phase'][entry['phase']]+=extras>0
    case['selected_extra_routes']+=extras;case['selection_list_changed_snapshots']+=trial[variant]['generic_diverse_selection_changed']
    case['raw_generated']+=sum(g['generated'] for g in trial['goals'])
    case['heap_cutoff_goal_instances']+=sum(g['stop']!=0 for g in trial['goals'])
    if variant=='strict':
     case['motion_feasible']+=sum(g['motion_feasible'] for g in trial['goals'])
     case['post_shortcut_unique']+=sum(g['strict_unique'] for g in trial['goals'])
     for g in trial['goals']:
      for candidate in g['candidates']:case['rejection_counts'].update(candidate['rejections'])
    else:
     case['post_shortcut_unique']+=sum(g['post_only_unique' if variant=='post_only' else 'no_motion_unique'] for g in trial['goals'])
   snap['trials'].append(short)
  snapshot_rows.append(snap)
 primary=cases[(6,'strict')]
 passed=(primary['positive_snapshots']>=6 and primary['positive_by_phase']['chronological_middle']>=2 and primary['positive_by_phase']['chronological_late']>=2)
 for case in cases.values():
  case['positive_by_phase']=dict(case['positive_by_phase'])
  if case['constraints']=='strict':case['rejection_counts']=dict(case['rejection_counts'])
  else:case['motion_feasible']=None;case['rejection_counts']=None
 return {'schema':'cerlab-i2-05-supply-summary-v1','protocol_sha256':state['protocol_sha256'],
 'snapshot_count':24,'combinations':72,'input_type':'single historical run execution-start snapshots; chronological phases, not independent seeds or exact planning replay',
 'repeat_exact_non_timing':True,'goal_instances':{'reachable':reachable,'unreachable':unreachable,'missing':missing},
 'primary_gate_passed':passed,'cases':list(cases.values()),'snapshots':snapshot_rows,
 'claims':{'candidate_supply_under_offline_operation_caps':passed,'online_50ms_feasibility':False,'actual_observation_improvement':False,'full_paired_pilot_complete':False},
 'next':'Preregister same-settings online budget admission and paired pilot; keep K=6/V1 limits. Pool12/24 and relaxed constraints are diagnostics only.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--protocol',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=summarize(a.protocol,a.results);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('primary gate:',result['primary_gate_passed'],'snapshots:',result['snapshot_count'],'combinations:',result['combinations'])
 return 0
if __name__=='__main__':raise SystemExit(main())
