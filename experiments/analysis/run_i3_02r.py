#!/usr/bin/env python3
"""One read-only I3-02R attribution over the frozen I3-02A artifacts."""
import argparse, hashlib, json, math, statistics, struct, subprocess
from collections import Counter
from pathlib import Path
from i3_segment_attribution import labeled_samples, spearman, sign, point_segment_distance, components6

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def exact_samples(expected, actual, tolerance):
    if len(expected)!=len(actual):return False
    for a,b in zip(expected,actual):
        if max(abs(a['position'][i]-b['position'][i]) for i in range(3))>tolerance:return False
        if abs(math.remainder(a['yaw']-b['yaw'],2*math.pi))>tolerance:return False
    return True

def map_header(path):
    with path.open('rb') as f:
        magic=f.read(8);schema=struct.unpack('<I',f.read(4))[0];version=struct.unpack('<Q',f.read(8))[0]
        resolution=struct.unpack('<d',f.read(8))[0]
        minimum=list(struct.unpack('<3d',f.read(24)));maximum=list(struct.unpack('<3d',f.read(24)))
        dimensions=list(struct.unpack('<3i',f.read(12)))
    assert magic[:7]==b'CR1MAP1' and schema==1
    return {'version':version,'resolution':resolution,'minimum':minimum,'maximum':maximum,'dimensions':dimensions}

def center(address,header):
    dy,dz=header['dimensions'][1],header['dimensions'][2]
    index=[address//(dy*dz),(address//dz)%dy,address%dz]
    return [header['minimum'][i]+(index[i]+.5)*header['resolution'] for i in range(3)]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output;out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parents[2]
    protocol_file=repo/'experiments/i3/I3_02R_PROTOCOL.json';protocol=json.loads(protocol_file.read_text())
    source=Path(protocol['source']);summary_file=source/'summary.json';batch_file=source/'batch_state.json'
    assert sha(summary_file)==protocol['source_summary_sha256'];assert sha(batch_file)==protocol['source_batch_sha256']
    for line in (source/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1);assert sha(Path(name))==digest
    prior=json.loads(summary_file.read_text());prior_batch=json.loads(batch_file.read_text())
    assert prior['decision']=='PROXY_NOT_SUPPORTED' and prior_batch['status']=='COMPLETE'
    i3a=json.loads((repo/'experiments/i3/I3_02A_PROTOCOL.json').read_text());case_by={c['sequence']:c for c in i3a['cases']}
    state_by={s['sequence']:s for s in prior['states']};phase=[]
    for seq in protocol['valid_states']:
        case=case_by[seq];snapshot=Path(case['directory']);request=json.loads((Path(i3a['source_root'])/('request_%06d.json'%seq)).read_text())
        assert case['snapshot_sha256']=={p.name:sha(p) for p in snapshot.iterdir() if p.is_file()}
        pool=json.loads((source/('s%03d_pool.json'%seq)).read_text());reference_input=json.loads((source/('s%03d_reference.input.json'%seq)).read_text());reference_output=json.loads((source/('s%03d_reference.json'%seq)).read_text())
        candidates=[]
        for rid in pool['pool']:
            record=pool['records'][rid];edge=record['edge'];path=record['path']
            candidate_input=json.loads((source/('s%03d_r%05d_full.input.json'%(seq,rid))).read_text())
            candidate_output=json.loads((source/('s%03d_r%05d_full.json'%(seq,rid))).read_text())
            ref_positions=[request['nodes'][i] for i in request['reference']];cand_positions=[request['nodes'][i] for i in path]
            ref_samples,ref_labels=labeled_samples(ref_positions,request['start_yaw'],request['terminal_yaw'],edge,False)
            cand_samples,cand_labels=labeled_samples(cand_positions,request['start_yaw'],request['terminal_yaw'],edge,True)
            tol=protocol['position_yaw_match_tolerance']
            assert exact_samples(ref_samples,reference_input['samples'],tol);assert exact_samples(cand_samples,candidate_input['samples'],tol)
            assert len(ref_labels)==len(reference_output['marginal_gains']);assert len(cand_labels)==len(candidate_output['marginal_gains'])
            ref_phase=Counter();cand_phase=Counter()
            for label,gain in zip(ref_labels,reference_output['marginal_gains']):ref_phase[label]+=gain
            for label,gain in zip(cand_labels,candidate_output['marginal_gains']):cand_phase[label]+=gain
            m0=sum(ref_phase[x] for x in ('replaced_edge','changed_exit'))
            mc=sum(cand_phase[x] for x in ('inserted_incoming','inserted_outgoing','changed_exit'))
            u0=reference_output['unique_gain']/pool['reference_motion']['time'];delta_time=record['motion']['time']-pool['reference_motion']['time']
            score=mc-m0-u0*delta_time
            candidates.append({'record_id':rid,'anchor':record['anchor'],'edge':edge,'path':path,'time':record['motion']['time'],'length':record['motion']['length'],'segment_score':score,'candidate_changed_marginal':mc,'reference_changed_marginal':m0,'candidate_phase_marginal':dict(cand_phase),'reference_phase_marginal':dict(ref_phase),'candidate_sample_count':len(cand_labels),'reference_sample_count':len(ref_labels)})
        eligible=[x for x in candidates if x['segment_score']>protocol['utility_tolerance']]
        selected=None if not eligible else min(eligible,key=lambda x:(-x['segment_score'],x['time'],x['length'],x['anchor'],x['edge'],x['record_id']))['record_id']
        phase.append({'sequence':seq,'selected_record_id':selected,'candidates':candidates})
    checkpoint={'schema':'i3-02r-preoracle-selection-v1','protocol_sha256':sha(protocol_file),'states':phase}
    checkpoint_file=out/'selection_checkpoint.json';checkpoint_file.write_text(json.dumps(checkpoint,indent=2)+'\n')
    checkpoint_sha=sha(checkpoint_file)
    states=[];all_scores=[];all_oracle=[];spatial=[]
    for pre in phase:
        seq=pre['sequence'];case=case_by[seq];snapshot=Path(case['directory']);request=json.loads((Path(i3a['source_root'])/('request_%06d.json'%seq)).read_text())
        pool=json.loads((source/('s%03d_pool.json'%seq)).read_text());ref=json.loads((source/('s%03d_reference.json'%seq)).read_text());ref_set=set(ref['unique_addresses']);u0=ref['unique_gain']/pool['reference_motion']['time']
        rows=[]
        for item in pre['candidates']:
            rid=item['record_id'];full=json.loads((source/('s%03d_r%05d_full.json'%(seq,rid))).read_text());addresses=set(full['unique_addresses'])
            delta_time=item['time']-pool['reference_motion']['time'];oracle=len(addresses)-len(ref_set)-u0*delta_time
            utility=len(addresses)/item['time'];row={**item,'oracle_net_value':oracle,'utility':utility,'utility_change':utility-u0,'downstream_residual':oracle-item['segment_score'],'sign_agrees':sign(oracle)==sign(item['segment_score'])}
            rows.append(row);all_scores.append(item['segment_score']);all_oracle.append(oracle)
        useful=[x for x in rows if x['utility']>u0+protocol['utility_tolerance']]
        oracle_choice=None if not useful else min(useful,key=lambda x:(-x['utility'],x['time'],x['length'],x['anchor'],x['edge'],x['record_id']))['record_id']
        geometry=state_by[seq]['selections_frozen_before_oracle']['geometry']
        selected=pre['selected_record_id'];selected_row=next((x for x in rows if x['record_id']==selected),None)
        state={'sequence':seq,'reference_utility':u0,'segment_choice':selected,'oracle_choice':oracle_choice,'geometry_choice':geometry,'exact_choice':selected==oracle_choice,'segment_selected_utility_change':0 if selected_row is None else selected_row['utility_change'],'candidates':rows}
        states.append(state)
        if oracle_choice is not None:
            row=next(x for x in rows if x['record_id']==oracle_choice);full=json.loads((source/('s%03d_r%05d_full.json'%(seq,oracle_choice))).read_text());added=set(full['unique_addresses'])-ref_set
            record=pool['records'][oracle_choice];nodes=request['nodes'];a=nodes[request['reference'][record['edge']]];anchor=nodes[record['anchor']];b=nodes[request['reference'][record['edge']+1]]
            header=map_header(snapshot/'map.bin');points=[center(v,header) for v in added]
            anchor_dist=[math.dist(p,anchor) for p in points];corridor_dist=[min(point_segment_distance(p,a,anchor),point_segment_distance(p,anchor,b)) for p in points]
            comps=components6(added,header['dimensions'])
            spatial.append({'sequence':seq,'record_id':oracle_choice,'added_voxels':len(added),'component_count':len(comps),'largest_component':comps[0] if comps else 0,'largest_component_fraction':comps[0]/len(added) if added else 0,'anchor_distance_median':statistics.median(anchor_dist) if anchor_dist else None,'corridor_distance_median':statistics.median(corridor_dist) if corridor_dist else None,'within_5m_anchor_fraction':sum(x<=protocol['camera_range_m_for_description'] for x in anchor_dist)/len(added) if added else None,'within_5m_corridor_fraction':sum(x<=protocol['camera_range_m_for_description'] for x in corridor_dist)/len(added) if added else None})
    rho=spearman(all_scores,all_oracle);agreement=sum(sign(a)==sign(b) for a,b in zip(all_scores,all_oracle))/len(all_scores)
    exact=sum(s['exact_choice'] for s in states);by_seq={s['sequence']:s for s in states}
    gates={'exact_choice_pass':exact==protocol['required_exact_state_choices'],'spearman_pass':rho is not None and rho>=protocol['spearman_min'],'sign_pass':agreement>=protocol['sign_agreement_min'],'state26_distinct_positive_pass':by_seq[26]['segment_choice']!=by_seq[26]['geometry_choice'] and by_seq[26]['segment_selected_utility_change']>protocol['utility_tolerance'],'state38_no_regression_pass':by_seq[38]['segment_choice']==by_seq[38]['oracle_choice']}
    passed=all(gates.values());decision='SEGMENT_SIGNAL_ONLY_REQUIRES_NEW_OPPORTUNITY_GENERATOR' if passed else 'CLOSE_CURRENT_SINGLE_ANCHOR_MECHANISM'
    result={'schema':'i3-02r-segment-attribution-v1','protocol_sha256':sha(protocol_file),'source_summary_sha256':sha(summary_file),'selection_checkpoint_sha256':checkpoint_sha,'states':states,'candidate_count':len(all_scores),'exact_state_choices':exact,'spearman_segment_vs_oracle':rho,'sign_agreement':agreement,'gates':gates,'decision':decision,'spatial_description':spatial,'camera_evaluations':0,'new_candidates':0,'new_simulation':False,'changes_i3_02a_decision':False,'limitations':['post-hoc mechanism diagnosis on already observed development artifacts','segment score consumes saved full-route path-history marginals and is not an implemented cheap selector','spatial distance omits field of view and occlusion','correlated candidates and five states are not statistical validation']}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'batch_state.json').write_text(json.dumps({'status':'COMPLETE','protocol_sha256':sha(protocol_file),'selection_checkpoint_sha256':checkpoint_sha,'decision':decision,'camera_evaluations':0,'new_candidates':0},indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('states','spatial_description')},indent=2))

if __name__=='__main__':main()
