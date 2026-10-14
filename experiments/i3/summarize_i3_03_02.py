#!/usr/bin/env python3
"""Paired state summaries; timing repeats never become independent state samples."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
from run_i3_03_02 import read, write, require, sha, validate

TOL=1e-9


def effective(trial,reference,k=None):
    if not trial['complete']:return reference
    values=[r['exact']['utility'] for r in trial.get('routes',[]) if r.get('exact',{}).get('valid')]
    if k is not None:values=values[:k]
    return max([reference]+values)


def comparison(rows,control,field='equal_count'):
    deltas=[r[field]['3']-r[field][str(control)] for r in rows]
    return {'states':len(deltas),'wins':sum(x>TOL for x in deltas),'ties':sum(abs(x)<=TOL for x in deltas),'losses':sum(x<-TOL for x in deltas),
            'mean_absolute_delta':statistics.mean(deltas) if deltas else None,'median_absolute_delta':statistics.median(deltas) if deltas else None,
            'mean_relative_delta_to_reference':statistics.mean([(r[field]['3']-r[field][str(control)])/r['reference_utility'] for r in rows if r['reference_utility']!=0]) if any(r['reference_utility']!=0 for r in rows) else None}


def passes(c):
    return c['states']>0 and c['wins']>=2 and c['mean_absolute_delta']>TOL and c['median_absolute_delta']>=-TOL


def verdict(engineering,value,budget):
    if not engineering:return 'EVIDENCE_INSUFFICIENT_ENGINEERING_FAILURE'
    if not value:return 'METHOD_NOT_SUPPORTED'
    return 'PROTOTYPE_SUPPORTED_EXECUTION_UNVERIFIED' if budget else 'PARTIAL_SUPPORT_OFFLINE_VALUE_ONLY'


def summarize(root):
    reg=read(root/'inputs.json');validate(reg);batch=read(root/'batch_state.json')
    require(batch['status']=='COMPLETE' and len(batch['completed_jobs'])==304,'Incomplete batch; preserve unfinished status')
    receipts={r['job']:r for r in batch['completed_jobs']};failures=[];rows=[];status=Counter();oracle=0;coarseQueries=0;maxScratch=0;maxRSS=0
    for c in reg['cases']:
        s=c['sequence'];data={}
        for regime in ('mechanism','budget'):
            for mode in range(4):
                name='s%03d_%s_m%d'%(s,regime,mode);receipt=receipts[name]
                if receipt.get('returncode')!=0:
                    failures.append(receipt);continue
                filename=root/(name+'.stdout.json');require(sha(filename)==receipt['output_sha256'],'Output changed')
                output=read(filename);data[(regime,mode)]=output
                maxRSS=max(maxRSS,receipt['peak_rss_kib'])
                for t in output['trials']:
                    status[(regime,mode,t['status'])]+=1;maxScratch=max(maxScratch,t['scratch_peak_bytes'])
                    require(t['oracle_match'],'Oracle mismatch')
                    if t['context_valid']:
                        require(t['safe'] and t['selected'],'Unsafe returned reference or selection')
                    if t['complete']:
                        require(t['reference']['valid'] and len(t['routes'])<=5,'Invalid completed output')
                        require(all(r.get('exact',{}).get('valid') for r in t['routes']),'Partial score used')
                        require(t['generation']['actions']<=12000 and t['generation']['coarse_queries']<=65,'Operation cap violation')
                        require(t['coarse_samples']<=10000 and t['coarse_voxel_visits']<=100000000,'Coarse query cap violation')
                        if regime=='budget':require(t['total_ms']<=500 and (mode==0 or t['generation_ms']<=50),'Completed trial exceeded deadline')
                    if mode!=3:require(t['coarse_samples']==t['coarse_voxel_visits']==0,'Control charged observation proxy')
                    if regime=='mechanism' and t['reference']['valid']:oracle+=1
                    coarseQueries+=t['generation']['coarse_queries']
        if not c['accepted_at_recording']:
            require(all(d['status']=='SKIP_NEGATIVE_CONTROL' and d['camera_queries']==0 for d in data.values()),'Negative control work')
            rows.append({'sequence':s,'status':'NEGATIVE_CONTROL','subset':c['subset'],'stage':c['stage']});continue
        if len(data)!=8:
            rows.append({'sequence':s,'status':'TOOL_ERROR','subset':c['subset'],'stage':c['stage']});continue
        trials={mode:data[('mechanism',mode)]['trials'][0] for mode in range(4)}
        if not all(t['context_valid'] for t in trials.values()):
            rows.append({'sequence':s,'status':'CONTEXT_INVALID','subset':c['subset'],'stage':c['stage'],'reasons':{str(m):t['reason'] for m,t in trials.items()}});continue
        if not all(t['reference']['valid'] for t in trials.values()):
            rows.append({'sequence':s,'status':'REFERENCE_INCOMPLETE','subset':c['subset'],'stage':c['stage']});continue
        u0=trials[0]['reference']['utility'];ref=trials[0]['reference']['unique_addresses']
        require(all(t['reference']['unique_addresses']==ref and abs(t['reference']['utility']-u0)<=TOL for t in trials.values()),'Reference parity')
        counts={m:sum(r.get('exact',{}).get('valid',False) for r in trials[m]['routes']) if trials[m]['complete'] else 0 for m in (1,2,3)}
        k=min(counts.values());row={'sequence':s,'status':'VALID','subset':c['subset'],'stage':c['stage'],'reference_utility':u0,'equal_actual_extra_scores_K':k,
            'actual_extra_counts':{str(m):n for m,n in counts.items()},'equal_count':{str(m):effective(t,u0,k) for m,t in trials.items()},
            'cap_results':{str(m):effective(t,u0) for m,t in trials.items()},'budget_results':{},'budget_complete':{},'generation_ms':{},'total_ms':{},'selected_details':{}}
        for mode,t in trials.items():
            row['generation_ms'][str(mode)]=t['generation_ms'];row['total_ms'][str(mode)]=t['total_ms']
            if t['complete'] and t['selected']!=read(c['request'])['reference']:
                chosen=next(r for r in t['routes'] if r['path']==t['selected']);obs=set(chosen['exact']['unique_addresses']);base=set(ref)
                row['selected_details'][str(mode)]={'layer':chosen['layer'],'new_voxels':len(obs-base),'lost_voxels':len(base-obs),'unique_gain':len(obs),'time':chosen['time'],'length':chosen['length'],'proxy_new':chosen['proxy_new'],'proxy_lost':chosen['proxy_lost']}
            bt=data[('budget',mode)]['trials'];row['budget_results'][str(mode)]=statistics.median(effective(x,u0) for x in bt)
            row['budget_complete'][str(mode)]=sum(x['complete'] for x in bt)
        rows.append(row)
    valid=[r for r in rows if r['status']=='VALID'];expanded=[r for r in valid if r['subset']=='expanded_development'];old=[r for r in valid if r['subset']=='historical_development']
    contrasts={name:{str(m):comparison(group,m) for m in (1,2)} for name,group in [('primary_expanded',expanded),('all_valid',valid),('old_development',old)]}
    value=all(passes(x) for x in contrasts['primary_expanded'].values())
    budget_contrasts={str(m):comparison(expanded,m,'budget_results') for m in (1,2)}
    budget_rate=sum(r['budget_complete']['3'] for r in valid)/(3*len(valid)) if valid else 0
    budget=budget_rate>=.9 and all(x['wins']>=2 for x in budget_contrasts.values())
    engineering=not failures and maxScratch<=268435456 and bool(valid)
    report={'task':'I3-03-02','verdict':verdict(engineering,value,budget),'engineering_passed':engineering,'mechanism_value_passed':value,'budget_admission_passed':budget,
            'input_states':38,'valid_states':len(valid),'primary_expanded_states':len(expanded),'state_statuses':dict(Counter(r['status'] for r in rows)),
            'primary_equal_count_comparisons':contrasts,'primary_budget_comparisons':budget_contrasts,'observation_budget_complete_fraction':budget_rate,
            'original_cap_comparisons':{str(m):comparison(expanded,m,'cap_results') for m in (1,2)},
            'stage_comparisons':{stage:{str(m):comparison([r for r in expanded if r['stage']==stage],m) for m in (1,2)} for stage in ('early','middle','late')},
            'oracle_reference_selected_checks':oracle,'peak_scratch_bytes':maxScratch,'peak_process_rss_kib':maxRSS,
            'trial_status_counts':[{'regime':regime,'mode':mode,'status':s,'count':n} for (regime,mode,s),n in sorted(status.items())],
            'tool_failures':failures,'cases':rows,'simulation_runs':0,'new_seeds':0,'method_revision_allowed':False,
            'limitations':['one historical static world/seed trajectory; correlated states','predicted frozen-map route utility only; actual observation/coverage/T95 untested',
                           'inserted anchors preserved in all controls; ordinary shortcut/B-spline not evaluated','same-machine pinned parallel timing still shares cache/memory/turbo',
                           'sparse internal proxy differs from dense final scorer and ignores unknown obstacles as specified','no post-result tuning or further tests authorized']}
    write(root/'summary.json',report);print(json.dumps({k:report[k] for k in ('verdict','engineering_passed','mechanism_value_passed','budget_admission_passed','valid_states','primary_expanded_states','observation_budget_complete_fraction','primary_equal_count_comparisons')},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();summarize(a.root)
