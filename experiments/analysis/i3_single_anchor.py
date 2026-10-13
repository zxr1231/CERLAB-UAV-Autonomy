"""Selector sees only anchor proxy/cost; full-route oracle is a separate phase."""
import math
MODES=('geometry','naive_marginal','residual_cost')
def choose(proxies,reference_unique,reference_time):
    if reference_time<=0 or not math.isfinite(reference_time):raise ValueError('invalid reference time')
    u0=reference_unique/reference_time
    rows=[]
    for p in proxies:
        if p['time']<=0 or not all(math.isfinite(p[k]) for k in ['time','length']):raise ValueError('invalid proxy cost')
        delta=max(0.,p['time']-reference_time)
        rows.append(dict(p,residual_score=p['new_voxels']-u0*delta))
    if not rows:return {m:None for m in MODES}
    tie=lambda p:(p['time'],p['length'],p['anchor'],p['edge'])
    # Marginal/residual ties deliberately omit length, per frozen method definition.
    rest=lambda p:(p['time'],p['anchor'],p['edge'])
    return {'geometry':min(rows,key=tie)['record_id'],
            'naive_marginal':min(rows,key=lambda p:(-p['new_voxels'],)+rest(p))['record_id'],
            'residual_cost':min(rows,key=lambda p:(-p['residual_score'],)+rest(p))['record_id']}

def route_effect(before,after,t0,time,proxy_new):
    a,b=set(before),set(after);u0=len(a)/t0;u=len(b)/time
    added=len(b-a);lost=len(a-b)
    return {'added':added,'lost':lost,'net_voxels':len(b)-len(a),'jaccard':len(a&b)/len(a|b) if a|b else 1.,
            'utility':u,'reference_utility':u0,'net_value':len(b)-len(a)-u0*(time-t0),
            'proxy_new_error':proxy_new-added,'raw_relative_rate':(u-u0)/u0 if u0 else None,
            'effective_utility':u if u>u0+1e-9 else u0,
            'effective_relative_rate':(u-u0)/u0 if u>u0+1e-9 and u0 else (0. if u0 else None),
            'final_choice':'extra' if u>u0+1e-9 else 'reference'}

def gates(states,tolerance=1e-9):
    valid=[s for s in states if s['status']=='COMPLETE']
    if len(valid)!=5:return {'decision':'ENGINEERING_FAIL','admit_timing_protocol':False}
    supply=[s['sequence'] for s in valid if any(r['utility']>s['reference_utility']+tolerance for r in s['evaluated'])]
    proxy=[s['sequence'] for s in valid if s['selectors']['residual_cost']['effective_utility']>s['reference_utility']+tolerance]
    difference=[s['sequence'] for s in valid if s['selectors']['residual_cost']['effective_utility']>s['selectors']['naive_marginal']['effective_utility']+tolerance]
    def mean(mode):
        a=[s['selectors'][mode]['effective_relative_rate'] for s in valid]
        return sum(a)/5 if all(x is not None for x in a) else None
    means={m:mean(m) for m in MODES};meanpass=means['residual_cost'] is not None and means['naive_marginal'] is not None and means['residual_cost']>=means['naive_marginal']
    decision='PASS_FOR_TIMING_PROTOCOL_ONLY'
    if len(supply)<2:decision='NO_USEFUL_SUPPLY_IN_THIS_SCOPE'
    elif len(proxy)<2:decision='PROXY_NOT_SUPPORTED'
    elif len(difference)<2 or not meanpass:decision='NO_DISTINCT_METHOD_SIGNAL'
    return {'decision':decision,'admit_timing_protocol':decision=='PASS_FOR_TIMING_PROTOCOL_ONLY',
            'useful_supply_states':supply,'residual_useful_states':proxy,'residual_beats_naive_and_reference_states':difference,
            'mean_effective_relative_rate':means,'mean_gate_pass':meanpass,'denominator':5}
