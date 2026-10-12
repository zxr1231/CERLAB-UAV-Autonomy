#!/usr/bin/env python3
"""Preregistered executed-prefix gate, preserves empty actual sets and frozen inputs."""
import argparse
import csv
import hashlib
import itertools
import json
import statistics
from pathlib import Path

from exploration_benchmark.actual_observation import write_actual_observation
from exploration_benchmark.observation_alignment import comparable_actual_set, set_metrics, spearman
from exploration_benchmark.r1_snapshot import load_frozen_map, load_snapshot
from exploration_benchmark.r1_visibility import LegacyVisibilityConfig
from exploration_benchmark.sensor_shadow_observation import build_sensor_shadow_observation, select_stage_intervals


def concordance(records, model):
    points = 0.0; pairs = 0
    for stage in ('early','middle','late'):
        for a,b in itertools.combinations([r for r in records if r['stage']==stage],2):
            actual = a['actual_per_meter']-b['actual_per_meter']
            if actual == 0: continue
            predicted = a[model]['predicted_per_meter']-b[model]['predicted_per_meter']
            points += .5 if predicted==0 else float(actual*predicted>0)
            pairs += 1
    return {'orderable_pair_count':pairs,'concordance':points/pairs if pairs else None}


def model_summary(records, model):
    if not records: return {'count':0,'per_meter_spearman':None,'median_jaccard':None,**concordance(records,model)}
    return {
        'count':len(records),
        'per_meter_spearman':spearman([r[model]['predicted_per_meter'] for r in records],[r['actual_per_meter'] for r in records]),
        'per_second_spearman':spearman([r[model]['predicted_per_second'] for r in records],[r['actual_per_second'] for r in records]),
        'count_spearman':spearman([r[model]['predicted_count'] for r in records],[r['actual_count'] for r in records]),
        'median_jaccard':statistics.median(r[model]['jaccard'] for r in records),
        'mean_jaccard':statistics.mean(r[model]['jaccard'] for r in records),
        'zero_actual_count':sum(r['actual_count']==0 for r in records),
        **concordance(records,model),
    }


def decision(summary, stage_counts, protocol, errors):
    checks = {
        'telemetry': not errors,
        'enough_comparisons':summary['count']>=protocol['minimum_valid'],
        'each_third':all(stage_counts.get(s,0)>=protocol['minimum_per_third'] for s in ('early','middle','late')),
        'per_meter_rank':summary['per_meter_spearman'] is not None and summary['per_meter_spearman']>=protocol['minimum_spearman_per_meter'],
        'orderable_pairs':summary['orderable_pair_count']>=protocol['minimum_orderable_pairs'],
        'within_third_order':summary['concordance'] is not None and summary['concordance']>=protocol['minimum_within_third_concordance'],
        'set_overlap':summary['median_jaccard'] is not None and summary['median_jaccard']>=protocol['minimum_median_jaccard'],
    }
    if not all(checks[k] for k in ('telemetry','enough_comparisons','each_third','orderable_pairs')):
        status='INCONCLUSIVE'
    else: status='PASS' if all(checks.values()) else 'FAIL'
    return {'status':status,'checks':checks}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run_directory',type=Path);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--output-directory',type=Path,required=True)
    args=parser.parse_args();raw=args.run_directory.resolve();output=args.output_directory.resolve()
    output.mkdir(parents=True,exist_ok=False)
    protocol=json.loads(args.protocol.read_text());project=Path(__file__).resolve().parents[2]
    for name,sha in protocol['files'].items():
        assert hashlib.sha256((project/name).read_bytes()).hexdigest()==sha, 'preregistered configuration changed: '+name
    tracked=['run.json','execution_intervals.csv','trajectory.csv','observation_deltas.jsonl','planning.csv','route_controls.jsonl']
    original={n:hashlib.sha256((raw/n).read_bytes()).hexdigest() for n in tracked}
    with (raw/'execution_intervals.csv').open() as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;intervals=list(reader)
    eligible=[r for r in intervals if r['valid'].lower()=='true' and int(r['global_sequence'])>0 and int(r['odom_count'])>=2 and float(r['executed_distance'])>=protocol['min_distance_m'] and float(r['duration_sim'])>0]
    selected=select_stage_intervals(eligible,protocol['samples_per_third'])
    (output/'selected_intervals.json').write_text(json.dumps({'selection':'registered eligibility and execution-order thirds, no information outcomes','eligible_count':len(eligible),'selected_ids_and_stage':selected,'eligible_interval_ids':[int(r['interval_id']) for r in eligible]},indent=2)+'\n')
    errors=[]
    missing=[int(r['interval_id']) for r in eligible if not (raw/'snapshots'/('execution_%06d'%int(r['interval_id']))).is_dir()]
    if missing:errors.append('qualifying execution snapshots missing: '+str(missing))
    actual_summary=write_actual_observation(raw,output)
    if actual_summary['status']!='VALID':errors.extend(actual_summary['errors'])
    actual={int(r['interval_id']):r for r in map(json.loads,(output/'actual_observation_sets.jsonl').read_text().splitlines())}
    view=output/'selected_prefix_view';view.mkdir();(view/'trajectory.csv').symlink_to(raw/'trajectory.csv')
    chosen=[r for r in intervals if int(r['interval_id']) in selected]
    predictions=[];records=[];snapshots={}
    mapping=project/'autonomous_flight/cfg/dynamic_exploration/mapping_param.yaml'
    for interval in chosen:
        identifier=int(interval['interval_id'])
        print('evaluating',identifier,selected[identifier],flush=True)
        with (view/'execution_intervals.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerow(interval)
        p=build_sensor_shadow_observation(view,raw/'snapshots',mapping,protocol['spacing_m'],protocol['yaw_spacing_rad'])
        if p['status']!='VALID':errors.extend(p['errors']);continue
        pred=p['intervals'][0];pred['stage']=selected[identifier];predictions.append(pred)
        folder=raw/'snapshots'/('execution_%06d'%identifier)
        snapshots[folder.name]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
        snapshot=load_snapshot(folder);grid=load_frozen_map(folder,snapshot)
        comparable,outside=comparable_actual_set(actual[identifier]['addresses'],grid,LegacyVisibilityConfig.from_planner(snapshot['planner']))
        if outside:errors.append('interval%d actual out of map'%identifier)
        distance=float(interval['executed_distance']);duration=float(interval['duration_sim'])
        record={'interval_id':identifier,'stage':selected[identifier],'executed_distance':distance,'duration_sim':duration,'actual_count':len(comparable),'actual_full_count':len(actual[identifier]['addresses']),'actual_per_meter':len(comparable)/distance,'actual_per_second':len(comparable)/duration}
        for model,key in [('legacy','legacy_addresses'),('sensor_shadow','addresses')]:
            metric=set_metrics(pred[key],comparable);metric['predicted_per_meter']=metric['predicted_count']/distance;metric['predicted_per_second']=metric['predicted_count']/duration;record[model]=metric
        records.append(record)
        print('completed',identifier,'actual',len(comparable),'shadow',len(pred['addresses']),flush=True)
    with (view/'execution_intervals.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(chosen)
    with (output/'sensor_shadow_sets.jsonl').open('w') as f:
        for pred in predictions:f.write(json.dumps(pred,sort_keys=True)+'\n')
    assert original=={n:hashlib.sha256((raw/n).read_bytes()).hexdigest() for n in tracked},'raw source changed'
    stage_counts={s:sum(r['stage']==s for r in records) for s in ('early','middle','late')}
    models={m:model_summary(records,m) for m in ('legacy','sensor_shadow')}
    decisions={m:decision(models[m],stage_counts,protocol,errors) for m in models}
    result={'schema':'i2-06-held-out-gate-v1','run_directory':str(raw),'protocol_sha256':hashlib.sha256(args.protocol.read_bytes()).hexdigest(),'eligible_count':len(eligible),'selected_count':len(chosen),'valid_count':len(records),'stage_counts':stage_counts,'errors':errors,'actual_integrity':actual_summary,'models':models,'decisions':decisions,'by_stage':{s:{m:model_summary([r for r in records if r['stage']==s],m) for m in models} for s in stage_counts},'intervals':records,'raw_input_sha256':original,'snapshot_file_sha256':snapshots,'limitations':['one dependent executed-prefix sample per interval, not unexecuted-route counterfactual','no FoV/speed/world tuning or favorable reruns','Unknown physical occlusion and level-body yaw approximation remain','No Coverage denominator for held-out world; no T80/T90/T95 claims']}
    (output/'held_out_gate.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'models':models,'decisions':decisions,'errors':errors},indent=2),flush=True)


if __name__=='__main__':main()
