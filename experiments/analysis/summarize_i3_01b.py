#!/usr/bin/env python3
"""Read-only summary of the first registered I3-01B batch."""
import argparse,collections,hashlib,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();state=json.loads((a.root/'batch_state.json').read_text());assert state['status']=='COMPLETE'
 rows=[];reasons=collections.Counter();raw=feasible=distinct=0;reference_pass=[];paired=[];budget_failures=[]
 for case in state['cases']:
  f=a.root/case['result_file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==case['result_sha256'];r=json.loads(f.read_text());row={'sequence':case['sequence'],'stage':case['stage'],'status':r['status']}
  if r['status']=='SKIP_B_NEGATIVE_CONTROL':
   assert case['sequence']==13 and r['camera_calls']==0 and not r['selected'] and not r['trials'];row['negative_control_pass']=True;rows.append(row);continue
  if r['status']!='CONTEXT_VALID':rows.append(row);continue
  supply=r['operation_supply'];raw+=supply['raw_count'];feasible+=supply['feasible_count'];distinct+=supply['distinct_count'];local=collections.Counter(x for c in supply['records'] for x in c['reasons']);reasons.update(local)
  row.update({'operation_supply':{k:supply[k] for k in ['raw_count','feasible_count','distinct_count','pops','stop']},'rejections':dict(local),'modes':{}})
  for mode,name in [(0,'reference'),(1,'generic'),(2,'diverse')]:
   t=[x for x in r['trials'] if x['mode']==mode];assert len(t)==3
   for x in t:
    assert x['oracle_match'] and x['motion_valid']
    if x['complete']:assert x['final_safe'] and x['camera_calls']==(1 if mode==0 else 2)
    if not x['alternative']['valid']:assert not x['alternative']['raw'] and not x['alternative']['unique'] and not x['alternative']['marginals']
   passed=all(x['complete'] and x['total_ms']<=500 and x['generation_ms']<=50 for x in t)
   row['modes'][name]={'statuses':[x['status'] for x in t],'completed_runs':sum(x['complete'] for x in t),'max_total_ms':max(x['total_ms'] for x in t),'max_generation_ms':max(x['generation_ms'] for x in t),'pass':passed}
  if row['modes']['reference']['pass']:reference_pass.append(case['sequence'])
  if row['modes']['generic']['pass'] and row['modes']['diverse']['pass']:paired.append(case['sequence'])
  if supply['distinct_count']>=2 and any('BUDGET' in status for m in ['generic','diverse'] for status in row['modes'][m]['statuses']):budget_failures.append(case['sequence'])
  rows.append(row)
 valid=[r for r in rows if r['status']=='CONTEXT_VALID'];supplied=[r['sequence'] for r in valid if r['operation_supply']['distinct_count']>=2]
 enough_refs=len(valid)>=3 and {r['stage'] for r in valid}=={'early','middle','late'}
 ref_pass=enough_refs and len(reference_pass)==len(valid)
 enough_supply=len(supplied)>=3 and {'middle','late'}<={r['stage'] for r in valid if r['sequence'] in supplied}
 enough_pairs=len(paired)>=3 and {'middle','late'}<={r['stage'] for r in valid if r['sequence'] in paired}
 admitted=ref_pass and enough_pairs
 decision='PASS_OFFLINE_ONLY' if admitted else ('INCONCLUSIVE_DATA' if not enough_refs else ('NO_GO_REFERENCE_COST' if not ref_pass else ('INCONCLUSIVE_SUPPLY' if not enough_supply else 'NO_GO_MULTI_COST')))
 out={'schema':'i3-01b-summary-v1','protocol_sha256':state['protocol_sha256'],'source_parent_commit':state['source_parent_commit'],'states':rows,'valid_reference_states':len(valid),'reference_cost_pass':ref_pass,'reference_pass_states':reference_pass,'structural_supply_states':supplied,'paired_two_candidate_states':paired,'cost_failure_where_supply_exists':budget_failures,'decision':decision,'admitted':admitted,'aggregate':{'raw_routes_including_references':raw,'motion_feasible_including_references':feasible,'post_shortcut_distinct_including_references':distinct,'motion_feasible_extras':feasible-len(valid),'distinct_extras':distinct-len(valid),'rejection_tags':dict(reasons)},'no_new_simulation':True,'no_kernel_change':True,'limitations':['one static-scene development corpus, not independent experimental validation','shortcut duplicate is geometric collapse, not proof of observation loss','insufficient actual candidate counts cannot support fixed-count H3','state27 has a real alternative but timed-out evaluation; no partial gain accepted','no retries/case replacement, no thresholds relaxed']}
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['reference_cost_pass','structural_supply_states','paired_two_candidate_states','cost_failure_where_supply_exists','decision','aggregate']},indent=2))
if __name__=='__main__':main()
